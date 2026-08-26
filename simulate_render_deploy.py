#!/usr/bin/env python3
"""
本地模拟 Render 部署流程，验证数据库迁移与静态文件收集是否成功。

该脚本镜像 render-build.sh 的步骤，并在每步后做断言：
  1. 安装依赖
  2. Django 部署检查 (manage.py check --deploy)
  3. 收集静态文件 (collectstatic)   ← 验证目标
  4. 应用数据库迁移 (migrate)        ← 验证目标
  5. 初始化内容 (seed)
  6. 创建默认管理员 (init_admin)
  7. WSGI 烟雾测试 (Django test client 访问首页)

环境变量会被覆盖为 Render 上的生产配置，但数据库指向一个独立的
test_deploy.sqlite3，避免污染开发用的 db.sqlite3。

用法：
    python simulate_render_deploy.py
    python simulate_render_deploy.py --skip-install   # 跳过 pip install
    python simulate_render_deploy.py --keep-db         # 保留测试数据库
"""
from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────────────────────────── #
ROOT = Path(__file__).resolve().parent
MANAGE = str(ROOT / "manage.py")
TEST_DB = ROOT / "test_deploy.sqlite3"
STATIC_ROOT = ROOT / "staticfiles"


# ── 终端颜色（Windows 10+ 支持 ANSI） ─────────────────────────────────────── #
class C:
    OK = "\033[92m"
    WARN = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


if sys.platform == "win32":
    os.system("")  # 启用 VT100 处理


def banner(msg: str) -> None:
    print(f"\n{C.BOLD}==> {msg}{C.END}")


def info(msg: str) -> None:
    print(f"{C.DIM}    {msg}{C.END}")


def ok(msg: str) -> None:
    print(f"{C.OK}    [PASS] {msg}{C.END}")


def fail(msg: str) -> None:
    print(f"{C.FAIL}    [FAIL] {msg}{C.END}")


def warn(msg: str) -> None:
    print(f"{C.WARN}    [WARN] {msg}{C.END}")


# ── 运行子进程 ─────────────────────────────────────────────────────────────── #
def run(cmd: list[str], env: dict, label: str) -> tuple[int, str]:
    """运行命令，返回 (returncode, output)。失败时不立即退出，由调用方决定。"""
    print(f"\n{C.BOLD}$ {' '.join(cmd)}{C.END}")
    proc = subprocess.run(
        cmd, cwd=ROOT, env=env,
        capture_output=True, text=True, encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout + proc.stderr).strip()
    if out:
        # 只打印最后 30 行，避免淹没终端
        lines = out.splitlines()
        for line in lines[-30:]:
            print(f"    {line}")
        if len(lines) > 30:
            print(f"    {C.DIM}... ({len(lines) - 30} 行已省略){C.END}")
    return proc.returncode, out


# ── 环境构造（模拟 Render） ──────────────────────────────────────────────────── #
def build_env() -> dict:
    env = os.environ.copy()
    # 与 render.yaml 对齐的生产配置
    env.update({
        "PYTHON_VERSION": "3.11.9",
        "SECRET_KEY": "test-only-secret-key-not-for-production-0123456789",
        "DEBUG": "False",
        "ALLOWED_HOSTS": "*.onrender.com,localhost,127.0.0.1",
        "CSRF_TRUSTED_ORIGINS": "https://*.onrender.com",
        "DATABASE_URL": f"sqlite:///{TEST_DB}",
        "ADMIN_INITIAL_PASSWORD": "TestAdminPass123!",
        "ADMIN_USERNAME": "admin",
        "ADMIN_EMAIL": "admin@example.com",
        "PORT": "10000",
        "WEB_CONCURRENCY": "2",
        "DJANGO_SETTINGS_MODULE": "aiyansite.settings",
    })
    return env


# ── 步骤 ───────────────────────────────────────────────────────────────────── #
def step_install_deps(env: dict, skip: bool) -> bool:
    if skip:
        warn("已通过 --skip-install 跳过依赖安装")
        return True
    banner("步骤 1/7 · 安装 Python 依赖")
    rc, _ = run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                env, "pip install")
    if rc != 0:
        fail("pip install 失败")
        return False
    ok("依赖安装完成")
    return True


def step_django_check(env: dict) -> bool:
    banner("步骤 2/7 · Django 部署检查 (check --deploy)")
    rc, out = run([sys.executable, MANAGE, "check", "--deploy"], env, "check")
    # check --deploy 在生产配置下会有若干 warning（如 SECURE_HSTS），不致命
    if rc != 0:
        fail("manage.py check 失败")
        return False
    ok("项目配置检查通过")
    return True


def step_collectstatic(env: dict) -> bool:
    banner("步骤 3/7 · 收集静态文件 (collectstatic)")
    # 清空旧的 staticfiles 以模拟首次部署
    if STATIC_ROOT.exists():
        shutil.rmtree(STATIC_ROOT)
        info("已清空旧的 staticfiles/")
    rc, out = run([sys.executable, MANAGE, "collectstatic", "--noinput", "-v2"],
                  env, "collectstatic")
    if rc != 0:
        fail("collectstatic 失败")
        return False

    # 验证 staticfiles 非空且包含核心资源
    if not STATIC_ROOT.exists():
        fail(f"staticfiles 目录不存在: {STATIC_ROOT}")
        return False
    files = list(STATIC_ROOT.rglob("*"))
    file_count = sum(1 for f in files if f.is_file())
    if file_count == 0:
        fail("collectstatic 完成但 staticfiles 为空")
        return False

    # 抽样检查典型静态资源
    has_css = any(STATIC_ROOT.rglob("*.css"))
    has_js = any(STATIC_ROOT.rglob("*.js"))
    ok(f"staticfiles 收集完成，共 {file_count} 个文件")
    info(f"包含 CSS: {has_css}  包含 JS: {has_js}")
    if not (has_css or has_js):
        warn("未发现 CSS/JS 文件，检查 STATICFILES_DIRS 配置")
    return True


def step_migrate(env: dict) -> bool:
    banner("步骤 4/7 · 应用数据库迁移 (migrate)")
    rc, out = run([sys.executable, MANAGE, "migrate", "--noinput"],
                  env, "migrate")
    if rc != 0:
        fail("migrate 失败")
        return False

    # 验证 migrations 表已记录迁移
    if not TEST_DB.exists():
        fail(f"迁移后数据库文件不存在: {TEST_DB}")
        return False
    conn = sqlite3.connect(TEST_DB)
    try:
        cur = conn.execute(
            "SELECT app, name FROM django_migrations ORDER BY app, id"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        fail("django_migrations 表为空")
        return False
    apps = {app for app, _ in rows}
    expected = {"auth", "contenttypes", "sessions", "admin", "website"}
    missing = expected - apps
    if missing:
        fail(f"缺少关键应用的迁移: {missing}")
        return False
    ok(f"已应用 {len(rows)} 条迁移，覆盖应用: {sorted(apps)}")
    return True


def step_seed(env: dict) -> bool:
    banner("步骤 5/7 · 初始化内容 (seed)")
    rc, out = run([sys.executable, MANAGE, "seed"], env, "seed")
    if rc != 0:
        # seed 标注为幂等且 render-build.sh 中 || true 容错
        warn("seed 命令返回非零（Render 中容错处理）")
        return True

    # 验证种子数据写入
    conn = sqlite3.connect(TEST_DB)
    try:
        cur = conn.execute("SELECT COUNT(*) FROM website_product")
        product_count = cur.fetchone()[0]
        cur = conn.execute("SELECT COUNT(*) FROM website_news")
        news_count = cur.fetchone()[0]
        cur = conn.execute("SELECT COUNT(*) FROM website_productcategory")
        cat_count = cur.fetchone()[0]
    finally:
        conn.close()
    ok(f"种子数据: 产品 {product_count}  新闻 {news_count}  产品分类 {cat_count}")
    if product_count == 0:
        warn("产品数据为空，检查 seed 命令")
    return True


def step_init_admin(env: dict) -> bool:
    banner("步骤 6/7 · 创建默认管理员 (init_admin)")
    rc, out = run([sys.executable, MANAGE, "init_admin"], env, "init_admin")
    if rc != 0:
        fail("init_admin 失败")
        return False

    # 验证 superuser 已创建
    conn = sqlite3.connect(TEST_DB)
    try:
        cur = conn.execute(
            "SELECT username, is_superuser FROM auth_user WHERE is_superuser=1"
        )
        users = cur.fetchall()
    finally:
        conn.close()
    if not users:
        fail("init_admin 完成但未找到 superuser")
        return False
    ok(f"已创建 superuser: {users[0][0]}")
    return True


def step_wsgi_smoke(env: dict) -> bool:
    banner("步骤 7/7 · WSGI 烟雾测试 (Django test client)")
    # 通过 test client 访问首页，验证 WSGI 应用能正常启动并渲染。
    # 写入临时脚本文件而非内联 -c，避免在日志中暴露整个 env 字典。
    test_script = ROOT / "_wsgi_smoke_test.py"
    test_script.write_text(
        "import django\n"
        "django.setup()\n"
        "from django.test import Client\n"
        # DEBUG=False 下：
        #  - test client 默认 Host 'testserver' 不在 ALLOWED_HOSTS，返回 400。
        #  - SECURE_SSL_REDIRECT=True 会把 HTTP 请求 301 到 HTTPS。
        # 解决：显式 Host=localhost + secure=True 模拟 HTTPS 请求。
        "c = Client(HTTP_HOST='localhost')\n"
        "r = c.get('/', secure=True)\n"
        "print('HTTP', r.status_code)\n"
        "assert r.status_code == 200, f'首页返回 {r.status_code}'\n"
        "print('BODY_LEN', len(r.content))\n",
        encoding="utf-8",
    )
    try:
        rc, out = run([sys.executable, str(test_script)], env, "wsgi smoke")
    finally:
        test_script.unlink(missing_ok=True)

    if rc != 0:
        fail("WSGI 烟雾测试失败")
        return False
    if "HTTP 200" not in out:
        fail("首页未返回 200")
        return False
    # 提取响应体大小
    body_len = ""
    for line in out.splitlines():
        if line.strip().startswith("BODY_LEN"):
            body_len = line.strip().split()[-1]
    ok("WSGI 应用启动正常，首页返回 200" +
       (f"，响应体 {body_len} 字节" if body_len else ""))
    return True


# ── 主流程 ─────────────────────────────────────────────────────────────────── #
def main() -> int:
    parser = argparse.ArgumentParser(description="模拟 Render 部署流程")
    parser.add_argument("--skip-install", action="store_true",
                        help="跳过 pip install 步骤")
    parser.add_argument("--keep-db", action="store_true",
                        help="运行结束不删除测试数据库")
    args = parser.parse_args()

    print(f"{C.BOLD}╔══════════════════════════════════════════════════════════╗{C.END}")
    print(f"{C.BOLD}║   AiYan 本地 Render 部署模拟器                          ║{C.END}")
    print(f"{C.BOLD}╚══════════════════════════════════════════════════════════╝{C.END}")
    info(f"项目根: {ROOT}")
    info(f"测试数据库: {TEST_DB}")

    # 清理上次遗留
    if TEST_DB.exists():
        TEST_DB.unlink()
        info("已删除上次的 test_deploy.sqlite3")

    env = build_env()
    results: list[tuple[str, bool]] = []

    results.append(("安装依赖", step_install_deps(env, args.skip_install)))
    results.append(("部署检查", step_django_check(env)))
    results.append(("收集静态文件", step_collectstatic(env)))
    results.append(("数据库迁移", step_migrate(env)))
    results.append(("初始化内容", step_seed(env)))
    results.append(("创建管理员", step_init_admin(env)))
    results.append(("WSGI 烟雾测试", step_wsgi_smoke(env)))

    # 汇总
    print(f"\n{C.BOLD}╔══════════════════════════════════════════════════════════╗{C.END}")
    print(f"{C.BOLD}║                       汇总报告                          ║{C.END}")
    print(f"{C.BOLD}╠══════════════════════════════════════════════════════════╣{C.END}")
    for name, passed in results:
        mark = f"{C.OK}PASS{C.END}" if passed else f"{C.FAIL}FAIL{C.END}"
        print(f"{C.BOLD}║{C.END}  {name:<12s}  {mark}")
    print(f"{C.BOLD}╚══════════════════════════════════════════════════════════╝{C.END}")

    all_passed = all(p for _, p in results)
    if all_passed:
        print(f"\n{C.OK}{C.BOLD}✓ 全部步骤通过，本地模拟 Render 部署成功。{C.END}")
    else:
        print(f"\n{C.FAIL}{C.BOLD}✗ 部分步骤失败，请按上方日志排查。{C.END}")

    # 清理
    if not args.keep_db and TEST_DB.exists():
        TEST_DB.unlink()
        info("已清理 test_deploy.sqlite3（使用 --keep-db 保留）")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
