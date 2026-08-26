"""
Seed the resource centre with metadata scraped from hpati.com.

The binary files (PDFs, ZIPs, etc.) stay hosted on the original site — we
only store metadata and link out via ``external_url``. Download passwords
are preserved as hints for users.

Idempotent: existing rows are updated in place by title.

Usage:
    python manage.py seed_resource
"""
from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from website.models import Product, Resource


# --------------------------------------------------------------------------- #
# Source data — taken from http://www.hpati.com/resources/ (Apr 2026 snapshot).
# 15 entries across 3 categories (doc / source / tool). Video section had no
# entries at scrape time.
# --------------------------------------------------------------------------- #
BASE = "http://www.hpati.com"

RESOURCES = [
    # ── 文档类 ──────────────────────────────────────────────────────────── #
    {
        'title': '物联网实验套件 AY-IOT KIT for CC3200 使用指南',
        'category': 'doc', 'product_slug': 'ay-iot-kit',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_doc_download/action_download_208.html',
        'published_at': date(2019, 12, 18),
        'order': 1,
    },
    {
        'title': '物联网实验套件 AY-IOT KIT for Raspberry 使用指南',
        'category': 'doc', 'product_slug': 'ay-iot-kit',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_doc_download/action_download_209.html',
        'published_at': date(2019, 12, 18),
        'order': 2,
    },
    {
        'title': 'AY-SEB 核心板 用户手册.pdf',
        'category': 'doc', 'product_slug': 'ay-seb-module',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_doc_download/action_download_167.html',
        'published_at': date(2019, 12, 18),
        'order': 3,
    },
    {
        'title': 'AY-SEB Kit 原理图.pdf',
        'category': 'doc', 'product_slug': 'ay-seb-kit',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_doc_download/action_download_156.html',
        'published_at': date(2019, 12, 18),
        'order': 4,
    },
    {
        'title': 'AY-SEB Kit 用户手册.pdf',
        'category': 'doc', 'product_slug': 'ay-seb-kit',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_doc_download/action_download_155.html',
        'published_at': date(2019, 12, 18),
        'order': 5,
    },

    # ── 代码类 ──────────────────────────────────────────────────────────── #
    {
        'title': 'M03507_Code_Example.rar',
        'category': 'source', 'product_slug': 'ay-mspm0g3507-c',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_source_download/action_download_217.html',
        'published_at': date(2024, 6, 17),
        'order': 1,
    },
    {
        'title': 'AY-SEB kit for CCS11.2.zip',
        'category': 'source', 'product_slug': 'ay-seb-kit',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_source_download/action_download_213.html',
        'published_at': date(2024, 6, 17),
        'order': 2,
    },
    {
        'title': 'MSEK_4_5529_CCS6 例程',
        'category': 'source', 'product_slug': 'ay-mse-kit',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_source_download/action_download_204.html',
        'published_at': date(2019, 12, 18),
        'order': 3,
    },
    {
        'title': 'MSEK_4_Tiva_CCS6 例程',
        'category': 'source', 'product_slug': 'ay-mse-kit',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_source_download/action_download_203.html',
        'published_at': date(2019, 12, 18),
        'order': 4,
    },
    {
        'title': 'AY-IOT KIT datasheet',
        'category': 'source', 'product_slug': 'ay-iot-kit',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_source_download/action_download_192.html',
        'published_at': date(2019, 12, 18),
        'order': 5,
    },

    # ── 工具软件视频 ────────────────────────────────────────────────────── #
    {
        'title': 'AY-IOT KIT 视频教程',
        'category': 'tool', 'product_slug': 'ay-iot-kit',
        'download_password': 'ri2x',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_tools_download/action_download_211.html',
        'published_at': date(2019, 12, 18),
        'order': 1,
    },
    {
        'title': 'AY-IOT KIT Blood Pressure 血压测量配套软件',
        'category': 'tool', 'product_slug': 'ay-iot-kit',
        'download_password': 'h916',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_tools_download/action_download_210.html',
        'published_at': date(2019, 12, 18),
        'order': 2,
    },
    {
        'title': 'energia 软件',
        'category': 'tool', 'product_slug': 'ay-iot-kit',
        'download_password': 'cwnp',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_tools_download/action_download_190.html',
        'published_at': date(2019, 12, 18),
        'order': 3,
    },
    {
        'title': 'MSEK 培训资料',
        'category': 'tool', 'product_slug': 'ay-mse-kit',
        'download_password': 'xxad',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_tools_download/action_download_172.html',
        'published_at': date(2019, 12, 18),
        'order': 4,
    },
    {
        'title': '高速 DDS 信号源（DDS5688）（PPT）',
        'category': 'tool', 'product_slug': None,
        'download_password': 'iddz',
        'file_size_hint': '',
        'external_url': f'{BASE}/ay_tools_download/action_download_162.html',
        'published_at': date(2019, 12, 18),
        'order': 5,
    },
]


# --------------------------------------------------------------------------- #
# Video resources — scraped from http://www.hpati.com/ay_video/ (4 pages, 42
# entries). Melody series demos + G2 teaching videos + sensor demos.
# product_slug mapping:
#   Melody*      → ay-iot-kit   (IoT kit sensor demos)
#   G2 口袋实验* → ay-g2pl-kit   (G2 platform teaching videos)
#   核心板*      → ay-seb-module (core board prep)
#   数字演示    → ay-g2pl-kit   (DC motor, step motor, etc. — G2 demos)
# --------------------------------------------------------------------------- #
VIDEOS = [
    # ── Melody 系列(8 条,无密码)— 关联物联网套件
    ('Getting Started Guide', '', f'{BASE}/ay_video/v76.html', 'ay-iot-kit', 1),
    ('MelodyADXL345（三轴加速度）', '', f'{BASE}/ay_video/v74.html', 'ay-iot-kit', 2),
    ('MelodyBP（血压）', '', f'{BASE}/ay_video/v82.html', 'ay-iot-kit', 3),
    ('MelodyHDC1080（温湿度）', '', f'{BASE}/ay_video/v75.html', 'ay-iot-kit', 4),
    ('MelodyLDC1000（电感）', '', f'{BASE}/ay_video/v77.html', 'ay-iot-kit', 5),
    ('MelodyLED（LED 控制）', '', f'{BASE}/ay_video/v79.html', 'ay-iot-kit', 6),
    ('MelodyLMT84（温度）', '', f'{BASE}/ay_video/v78.html', 'ay-iot-kit', 7),
    ('MelodyOPT3001（光照度）', '', f'{BASE}/ay_video/v80.html', 'ay-iot-kit', 8),
    ('MelodyStepMotor（步进电机）', '', f'{BASE}/ay_video/v81.html', 'ay-iot-kit', 9),

    # ── G2 口袋实验平台教学视频(16 条,密码 G2xx)
    ('G2 口袋实验平台教学视频 4', 'G24', f'{BASE}/ay_video/v41.html', 'ay-g2pl-kit', 10),
    ('G2 口袋实验平台教学视频 5', 'G25', f'{BASE}/ay_video/v40.html', 'ay-g2pl-kit', 11),
    ('G2 口袋实验平台教学视频 6', 'G26', f'{BASE}/ay_video/v39.html', 'ay-g2pl-kit', 12),
    ('G2 口袋实验平台教学视频 7.1', 'G271', f'{BASE}/ay_video/v42.html', 'ay-g2pl-kit', 13),
    ('G2 口袋实验平台教学视频 7.2', 'G272', f'{BASE}/ay_video/v43.html', 'ay-g2pl-kit', 14),
    ('G2 口袋实验平台教学视频 7.3', 'G273', f'{BASE}/ay_video/v44.html', 'ay-g2pl-kit', 15),
    ('G2 口袋实验平台教学视频 8.1', 'G281', f'{BASE}/ay_video/v45.html', 'ay-g2pl-kit', 16),
    ('G2 口袋实验平台教学视频 8.2', 'G282', f'{BASE}/ay_video/v38.html', 'ay-g2pl-kit', 17),
    ('G2 口袋实验平台教学视频 10', 'G210', f'{BASE}/ay_video/v46.html', 'ay-g2pl-kit', 18),
    ('G2 口袋实验平台教学视频 11', 'G211', f'{BASE}/ay_video/v47.html', 'ay-g2pl-kit', 19),
    ('G2 口袋实验平台教学视频 12', 'G212', f'{BASE}/ay_video/v48.html', 'ay-g2pl-kit', 20),
    ('G2 口袋实验平台教学视频 14', 'G214', f'{BASE}/ay_video/v49.html', 'ay-g2pl-kit', 21),
    ('G2 口袋实验平台教学视频 17', 'G217', f'{BASE}/ay_video/v50.html', 'ay-g2pl-kit', 22),
    ('G2 口袋实验平台教学视频 19', 'G219', f'{BASE}/ay_video/v51.html', 'ay-g2pl-kit', 23),
    ('G2 口袋实验平台教学视频 21.1', 'G2211', f'{BASE}/ay_video/v52.html', 'ay-g2pl-kit', 24),
    ('G2 口袋实验平台教学视频 21.2', 'G2212', f'{BASE}/ay_video/v53.html', 'ay-g2pl-kit', 25),
    ('G2 口袋实验平台教学视频 22', 'G222', f'{BASE}/ay_video/v54.html', 'ay-g2pl-kit', 26),

    # ── G2 暑期培训录像
    ('G2 口袋实验平台暑期培训录像', 'Msp430', f'{BASE}/ay_video/v55.html', 'ay-g2pl-kit', 27),

    # ── 核心板相关(关联 AY-SEB Module)
    ('核心板', '', f'{BASE}/ay_video/v57.html', 'ay-seb-module', 28),
    ('核心板准备', '', f'{BASE}/ay_video/v58.html', 'ay-seb-module', 29),

    # ── G2 数字演示(11 条,DC Motor 等)
    ('1. DC Motor（直流电机演示）', '', f'{BASE}/ay_video/v73.html', 'ay-g2pl-kit', 30),
    ('2. Step Motor（步进电机演示）', '', f'{BASE}/ay_video/v72.html', 'ay-g2pl-kit', 31),
    ('3. Ultrasonic（超声波演示）', '', f'{BASE}/ay_video/v71.html', 'ay-g2pl-kit', 32),
    ('4. White LED（白光 LED 演示）', '', f'{BASE}/ay_video/v70.html', 'ay-g2pl-kit', 33),
    ('5. Accel Meter（加速度计演示）', '', f'{BASE}/ay_video/v69.html', 'ay-g2pl-kit', 34),
    ('6. Infrared（红外演示）', '', f'{BASE}/ay_video/v68.html', 'ay-g2pl-kit', 35),
    ('7. Recorder（录音演示）', '', f'{BASE}/ay_video/v67.html', 'ay-g2pl-kit', 36),
    ('8. Elec scale（电子秤演示）', '', f'{BASE}/ay_video/v66.html', 'ay-g2pl-kit', 37),
    ('9. Triode tracer（三极管特性图示仪）', '', f'{BASE}/ay_video/v65.html', 'ay-g2pl-kit', 38),
    ('10. Music Display（音乐演奏演示）', 'G2', f'{BASE}/ay_video/v64.html', 'ay-g2pl-kit', 39),
    ('11. Miscell Demo（综合演示）', '', f'{BASE}/ay_video/v63.html', 'ay-g2pl-kit', 40),

    # ── 杂项
    ('menu（菜单演示）', '', f'{BASE}/ay_video/v62.html', 'ay-g2pl-kit', 41),
    ('prepare（预备演示）', '', f'{BASE}/ay_video/v61.html', 'ay-g2pl-kit', 42),
]


# --------------------------------------------------------------------------- #
# Command
# --------------------------------------------------------------------------- #
class Command(BaseCommand):
    help = 'Seed resource centre with metadata scraped from hpati.com.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            'Seeding resource centre…'
        ))

        # Preload product slugs → pk for FK linking.
        slug_to_pk = {
            p.slug: p for p in Product.objects.all()
        }

        created_count = 0
        updated_count = 0
        total = 0

        # ── 文档/代码/工具(15 条)────────────────────────────────── #
        for r in RESOURCES:
            total += 1
            product = slug_to_pk.get(r.get('product_slug')) if r.get('product_slug') else None
            defaults = {
                'category': r['category'],
                'description': r.get('description', ''),
                'download_password': r.get('download_password', ''),
                'file_size_hint': r.get('file_size_hint', ''),
                'external_url': r['external_url'],
                'product': product,
                'published_at': r.get('published_at'),
                'order': r.get('order', 0),
                'is_published': True,
            }
            obj, created = Resource.objects.update_or_create(
                title=r['title'], defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        # ── 视频资源(42 条)────────────────────────────────────── #
        for title, password, external_url, product_slug, order in VIDEOS:
            total += 1
            product = slug_to_pk.get(product_slug)
            defaults = {
                'category': 'video',
                'description': '',
                'download_password': password,
                'file_size_hint': '',
                'external_url': external_url,
                'product': product,
                'published_at': None,
                'order': order,
                'is_published': True,
            }
            obj, created = Resource.objects.update_or_create(
                title=title, defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'  · {created_count} 新建  {updated_count} 更新  共 {total} 条'
        ))
