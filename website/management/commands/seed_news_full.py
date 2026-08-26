"""
Seed real news content (title + body) scraped from hpati.com.

The base ``seed`` command only stores placeholder bodies for news articles
(see ``seed.py`` ``INDUSTRY_NEWS`` / ``COMPANY_NEWS``). This command goes to
hpati.com, walks the news listings + pagination, downloads every article
detail page and stores the real HTML body.

Default behaviour deletes every existing News row first, so the table is a
clean mirror of hpati.com. This is safe — News has no inbound foreign keys.

Usage:
    python manage.py seed_news_full           # clear + re-fetch all 53 articles
    python manage.py seed_news_full --keep    # update by slug, leave others
    python manage.py seed_news_full --max 5   # DEBUG: only first 5 per section
"""
from __future__ import annotations

import re
import urllib.request
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from website.models import News, NewsCategory


BASE = "http://www.hpati.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AiYanSiteNewsBot/1.0"
    )
}

# Map local category slug → hpati.com section path.
SECTIONS = [
    ("company-news", "/companynews/"),
    ("industry-news", "/industrynews/"),
]


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


# --------------------------------------------------------------------------- #
# Listing crawl — collect every nXX.html link from the index + paginated pages
# --------------------------------------------------------------------------- #
def collect_article_ids(section_path: str, max_pages: int = 12) -> list[str]:
    """Return sorted nXX.html IDs reachable from the section index."""
    found: set[str] = set()
    # Index page.
    html = fetch(f"{BASE}{section_path}")
    found.update(re.findall(
        rf'{re.escape(section_path)}(n\d+\.html)', html
    ))
    # Paginated pages: /companynews/2/, /companynews/3/, ...
    for p in range(1, max_pages + 1):
        try:
            page_html = fetch(f"{BASE}{section_path}{p}/")
        except Exception:
            break
        new_ids = re.findall(
            rf'{re.escape(section_path)}(n\d+\.html)', page_html
        )
        if not new_ids:
            break
        found.update(new_ids)
    # Sort numerically for stable ordering.
    return sorted(found, key=lambda s: int(re.search(r'\d+', s).group()))


# --------------------------------------------------------------------------- #
# Detail page parsing
# --------------------------------------------------------------------------- #
def parse_detail(html: str) -> tuple[str | None, object, str]:
    """Return (title, published_at date, body HTML)."""
    # Title — prefer <h1>, fall back to <h2>.
    title = None
    m = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    if m:
        title = m.group(1).strip()
    if not title:
        m = re.search(r'<h2[^>]*>([^<]+)</h2>', html)
        if m:
            title = m.group(1).strip()

    # Published date.
    published_at = None
    m = re.search(r'(20\d{2}[-./]\d{1,2}[-./]\d{1,2})', html)
    if m:
        raw = m.group(1).replace('.', '-')
        try:
            published_at = datetime.strptime(raw, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Body: take everything between the first <p> and the "相关" heading.
    body_start = html.find('<p')
    rel_match = re.search(r'<h\d[^>]*>\s*相关', html, re.IGNORECASE)
    body_end = rel_match.start() if rel_match else len(html)
    body_html = ''
    if body_start > 0:
        body = html[body_start:body_end]
        paragraphs = re.findall(r'<p[^>]*>([\s\S]*?)</p>', body)
        clean = []
        for p in paragraphs:
            text = re.sub(r'<[^>]+>', '', p).strip()
            if text and len(text) > 5:
                clean.append(f'<p>{text}</p>')
        body_html = '\n'.join(clean)
    return title, published_at, body_html


# --------------------------------------------------------------------------- #
# Command
# --------------------------------------------------------------------------- #
class Command(BaseCommand):
    help = '从 hpati.com 抓取所有新闻的真实标题、日期、正文 HTML 写入数据库。'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep', action='store_true',
            help='保留现有新闻,只按 slug 更新匹配的条目(不删除其他)。',
        )
        parser.add_argument(
            '--max', type=int, default=0,
            help='每个分类最多抓取多少条(0 表示全部,调试用)。',
        )

    def handle(self, *args, **options):
        keep = options['keep']
        max_per = options['max']

        self.stdout.write(self.style.MIGRATE_HEADING(
            '从 hpati.com 抓取真实新闻正文…'
        ))

        if not keep:
            deleted, _ = News.objects.all().delete()
            self.stdout.write(f'  · 已清空 {deleted} 条旧新闻')

        stats = {'created': 0, 'updated': 0, 'failed': 0}

        for cat_slug, section_path in SECTIONS:
            try:
                cat = NewsCategory.objects.get(slug=cat_slug)
            except NewsCategory.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'  · 跳过 {cat_slug}:分类不存在,请先跑 seed 命令'
                ))
                continue

            self.stdout.write(f'  · 扫描 {section_path} 列表 + 分页…')
            try:
                nids = collect_article_ids(section_path)
            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f'    列表抓取失败: {exc}'
                ))
                continue

            if max_per:
                nids = nids[:max_per]
            self.stdout.write(f'    发现 {len(nids)} 条候选文章')

            for nid in nids:
                url = f"{BASE}{section_path}{nid}"
                try:
                    html = fetch(url)
                    title, published_at, body = parse_detail(html)
                    if not title or not body:
                        stats['failed'] += 1
                        continue

                    # Stable slug derived from the hpati.com article ID —
                    # guarantees uniqueness across re-runs.
                    nid_num = re.search(r'\d+', nid).group()
                    slug = f'news-{nid_num}'

                    # Strip HTML for a plain-text excerpt (first 180 chars).
                    plain = re.sub(r'<[^>]+>', '', body).strip()
                    excerpt = plain[:180].rstrip() + ('…' if len(plain) > 180 else '')

                    obj, created = News.objects.update_or_create(
                        slug=slug,
                        defaults={
                            'title': title,
                            'body': body,
                            'excerpt': excerpt,
                            'category': cat,
                            'published_at': published_at,
                            'is_published': True,
                        },
                    )
                    if created:
                        stats['created'] += 1
                    else:
                        stats['updated'] += 1
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(
                        f'    {nid} 失败: {exc}'
                    ))
                    stats['failed'] += 1

        self.stdout.write(self.style.SUCCESS(
            f'  · 新建 {stats["created"]}  更新 {stats["updated"]}  '
            f'失败 {stats["failed"]}'
        ))
