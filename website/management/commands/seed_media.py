"""
Seed media assets (product covers, gallery, site logo) from hpati.com.

The original seed command intentionally leaves ImageField / FileField empty
(see website/management/commands/seed.py). This command fills them in by
scraping the public hpati.com pages and attaching the downloaded images to
the matching database records via Django's storage API.

Idempotent: re-running replaces existing attachments with freshly downloaded
files. Old files on disk are left in place (Django default); purge media/
manually if you want a clean slate.

Usage:
    python manage.py seed_media            # products + logo
    python manage.py seed_media --logo-only # just the site logo
    python manage.py seed_media --skip-gallery  # covers only, no extra shots
"""
from __future__ import annotations

import io
import re
import urllib.request
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from website.models import Product, ProductImage, SiteSetting


# --------------------------------------------------------------------------- #
# hpati.com → local slug mapping (based on the 7 products in seed.py).
# --------------------------------------------------------------------------- #
BASE = "http://www.hpati.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AiYanSiteMigrationBot/1.0"
    )
}

PRODUCT_URL_TO_SLUG = {
    "/products_line/product_62.html": "ay-smart-car",
    "/products_line/product_58.html": "ay-iot-kit",
    "/products_line/product_63.html": "ay-mspm0g3507-c",
    "/ay_competition_kit/product_35.html": "ay-mse-kit",
    "/ay_power/product_55.html": "ay-apower-kit",
    "/ay_scm_pack/product_53.html": "ay-scmp-kit",
    "/products_line/product_59.html": "sword4-0",
    # 7 个原本缺失的产品,补齐至原网站 13 个
    "/ay_teaching_kit/product_52.html": "mooc-ee-practice-kit",
    "/products_line/product_49.html": "ay-seb-module",
    "/ay_msp430/product_47.html": "ay-seb-kit",
    "/ay_scm_pack/product_33.html": "ay-g2pl-kit",
    "/ay_bluetooth/product_32.html": "ay-cc2564-evm",
    "/ay_signal_chain/product_46.html": "ay-tpa3112-evm",
    "/ay_msp430/product_44.html": "ay-ldc1000",
}

# Logo URL on the original site.
LOGO_PATH = "/skins/aiyan_model/images/logo.png"


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def fetch_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def abs_url(src: str) -> str:
    if src.startswith("http"):
        return src
    if src.startswith("//"):
        return "http:" + src
    return BASE + src if src.startswith("/") else f"{BASE}/{src}"


# --------------------------------------------------------------------------- #
# Image extraction
# --------------------------------------------------------------------------- #
def extract_product_images(html: str) -> list[str]:
    """Return de-duplicated /upload/ image URLs, preferring `m_` medium size.

    hpati.com stores three sizes per image:
        /upload/202406/20240617115828191.jpg      (original)
        /upload/202406/m_20240617115828191.jpg     (medium)
        /upload/202406/s_20240617115828191.jpg     (small thumb)
    We keep the `m_` version; if only `s_` is present we use it. Non-product
    images (logo, language flags) are excluded by the /upload/ prefix filter.

    Crucially, we cut off the "相关产品" (related products) section at the end
    of each detail page — those images belong to other products and would
    otherwise pollute this product's gallery.
    """
    # Truncate at "相关产品" heading if present.
    rel_match = re.search(r'<h\d[^>]*>\s*相关产品', html, re.IGNORECASE)
    if rel_match:
        html = html[:rel_match.start()]

    all_imgs = re.findall(r'<img[^>]*src="([^"]+)"', html)
    uploads = [src for src in all_imgs if "/upload/" in src]
    if not uploads:
        return []

    # Group by base filename (strip m_ or s_ prefix), prefer m_.
    grouped: dict[str, str] = {}
    for src in uploads:
        # /upload/202406/m_20240617115828191.jpg -> dir=202406, file=m_xxx.jpg
        match = re.search(r"/upload/(\d+)/([ms]_)?(.+)$", src)
        if not match:
            continue
        subdir, prefix, basename = match.groups()
        key = f"{subdir}/{basename}"
        existing = grouped.get(key)
        # Prefer m_ over s_; never overwrite with s_ if we have m_.
        if existing and existing.startswith("m_") and prefix != "m_":
            continue
        grouped[key] = src  # keep last seen (HTML order is stable)

    # Preserve first-seen order.
    seen = set()
    ordered: list[str] = []
    for src in uploads:
        if src in seen:
            continue
        seen.add(src)
        ordered.append(src)

    # After dedup by base name, pick m_ where available.
    final: list[str] = []
    picked_keys: set[str] = set()
    for src in ordered:
        match = re.search(r"/upload/(\d+)/([ms]_)?(.+)$", src)
        if not match:
            continue
        subdir, prefix, basename = match.groups()
        key = f"{subdir}/{basename}"
        if key in picked_keys:
            continue
        # If this is the s_ version but m_ also seen, skip (m_ was added first).
        if prefix == "s_" and key in {k.split("/", 1)[1] for k in picked_keys}:
            continue
        final.append(src)
        picked_keys.add(key)
    return final


# --------------------------------------------------------------------------- #
# Command
# --------------------------------------------------------------------------- #
class Command(BaseCommand):
    help = (
        "Download product covers, gallery images, and the site logo from "
        "hpati.com and attach them to the matching database records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--logo-only", action="store_true",
            help="Only refresh the site logo, skip products.",
        )
        parser.add_argument(
            "--skip-gallery", action="store_true",
            help="Download only the cover (first image) per product.",
        )

    def handle(self, *args, **options):
        logo_only = options["logo_only"]
        skip_gallery = options["skip_gallery"]

        self.stdout.write(self.style.MIGRATE_HEADING(
            "Seeding media assets from hpati.com…"
        ))

        # ── Site logo ─────────────────────────────────────────────────── #
        try:
            self._seed_logo()
        except Exception as exc:
            self.stdout.write(self.style.WARNING(
                f"  · logo: 跳过 ({exc})"
            ))

        if logo_only:
            self.stdout.write(self.style.SUCCESS("Done (logo only)."))
            return

        # ── Products ─────────────────────────────────────────────────── #
        ok, fail, skipped = 0, 0, 0
        for path, slug in PRODUCT_URL_TO_SLUG.items():
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"  · {slug}: 本地数据库未找到，跳过"
                ))
                skipped += 1
                continue

            try:
                count = self._seed_product(product, path, skip_gallery)
                self.stdout.write(
                    f"  · {slug}: 下载 {count} 张图片"
                )
                ok += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f"  · {slug}: 失败 ({exc})"
                ))
                fail += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n完成: 成功 {ok}  失败 {fail}  跳过 {skipped}"
        ))

    # ── Logo ───────────────────────────────────────────────────────────── #
    def _seed_logo(self) -> None:
        url = abs_url(LOGO_PATH)
        data = fetch_bytes(url)
        site = SiteSetting.get()
        ext = Path(LOGO_PATH).suffix.lower()  # .png
        # Clear previous to avoid name collisions on re-run.
        if site.logo:
            site.logo.delete(save=False)
        site.logo.save(f"logo{ext}", ContentFile(data), save=True)
        self.stdout.write(self.style.SUCCESS(
            f"  · logo: {len(data)} bytes → {site.logo.name}"
        ))

    # ── Product cover + gallery ────────────────────────────────────────── #
    def _seed_product(self, product: Product, detail_path: str,
                     skip_gallery: bool) -> int:
        html = fetch_text(abs_url(detail_path))
        img_urls = extract_product_images(html)
        if not img_urls:
            return 0

        downloaded = 0

        # First image = cover.
        cover_url = abs_url(img_urls[0])
        cover_data = fetch_bytes(cover_url)
        ext = Path(cover_url).suffix.lower() or ".jpg"
        if product.cover:
            product.cover.delete(save=False)
        product.cover.save(f"cover{ext}", ContentFile(cover_data), save=True)
        downloaded += 1

        if skip_gallery:
            return downloaded

        # Remaining images = gallery. Replace existing shots on re-run.
        product.images.all().delete()
        for i, src in enumerate(img_urls[1:], start=1):
            try:
                data = fetch_bytes(abs_url(src))
            except Exception:
                # Skip a single broken image instead of failing the whole run.
                continue
            ext = Path(src).suffix.lower() or ".jpg"
            caption = f"{product.name} 图{i}"
            pi = ProductImage(product=product, caption=caption, order=i)
            pi.image.save(f"shot-{i}{ext}", ContentFile(data), save=True)
            downloaded += 1

        return downloaded
