"""
Download all resource files from hpati.com into local media storage.

The ``external_url`` on hpati.com looks like ``action_download_208.html`` but
actually returns the binary file (PDF/ZIP/etc.) directly — no page parsing or
password form needed. This command walks every Resource row, downloads the
file, and attaches it to ``Resource.file`` via Django's storage API so the
public site can serve it from local media without depending on hpati.com.

Idempotent: re-running re-downloads and replaces existing files.

Usage:
    python manage.py seed_resource_files            # all resources
    python manage.py seed_resource_files --force     # re-download even if file exists
    python manage.py seed_resource_files --limit 5   # only first 5 (testing)
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from website.models import Resource


HEADERS = {
    "User-Agent": "Mozilla/5.0 (AiYanSiteMigrationBot/1.0)"
}

# Mime → extension hint, used when the URL has a misleading .html suffix.
EXT_BY_MAGIC = {
    b"%PDF": ".pdf",
    b"PK\x03\x04": ".zip",
    b"Rar!\x1a\x07": ".rar",
    b"\x1f\x8b": ".gz",
    b"7z\xbc\xaf\x27\x1c": ".7z",
    b"MZ": ".exe",
}


def sniff_ext(data: bytes, url: str) -> str:
    """Infer file extension from magic bytes, falling back to the URL."""
    for magic, ext in EXT_BY_MAGIC.items():
        if data.startswith(magic):
            return ext
    # URL might carry a real extension despite the .html disguise.
    from urllib.parse import urlparse
    path = urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext and ext not in (".html", ".htm", ".php", ".asp"):
        return ext
    return ".bin"


def fetch_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


class Command(BaseCommand):
    help = (
        "Download every Resource's external_url file into local media storage, "
        "so the site no longer depends on hpati.com for downloads."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true",
            help="Re-download even if a local file already exists.",
        )
        parser.add_argument(
            "--limit", type=int, default=0,
            help="Only process the first N resources (0 = all).",
        )

    def handle(self, *args, **options):
        force = options["force"]
        limit = options["limit"]

        qs = Resource.objects.all().order_by("category", "order")
        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Downloading resource files ({total} items)…"
        ))

        ok, skipped, failed = 0, 0, 0
        for r in qs:
            # Skip if already has a local file and not forcing.
            if r.file and not force:
                self.stdout.write(f"  · {r.title[:40]}: 已有本地文件，跳过")
                skipped += 1
                continue

            url = r.external_url
            try:
                data = fetch_bytes(url)
            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f"  · {r.title[:40]}: 下载失败 ({exc})"
                ))
                failed += 1
                continue

            ext = sniff_ext(data, url)
            # Build a safe filename from the title.
            from django.utils.text import slugify
            base = slugify(r.title) or f"resource-{r.pk}"
            # Truncate to avoid filesystem path limits.
            base = base[:80]
            filename = f"{base}{ext}"

            # Replace existing file on re-runs.
            if r.file:
                r.file.delete(save=False)
            r.file.save(filename, ContentFile(data), save=True)

            size_kb = len(data) // 1024
            self.stdout.write(self.style.SUCCESS(
                f"  · {r.title[:40]}: {size_kb} KB → {r.file.name}"
            ))
            ok += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n完成: 下载 {ok}  跳过 {skipped}  失败 {failed}"
        ))
