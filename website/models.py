"""
Database models for the AiYan website.

The schema mirrors the original hpati.com content but drops the user forum
entirely. Everything visible on the public site is editable from the Django
admin, and all binary assets (product images, gallery shots, downloadable
documents) are stored via FileField/ImageField under ``media/``.
"""
from __future__ import annotations

import os

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


# --------------------------------------------------------------------------- #
# Helpers — keep uploaded files organised on disk instead of one flat dump.
# These must be top-level (not closures) so Django's migration writer can
# serialise a stable import path for each ``upload_to`` callable.
# --------------------------------------------------------------------------- #
def _path_for(instance, filename: str, subdir: str) -> str:
    """Build a tidy media path: ``<subdir>/<owner-slug>/<safe-name><ext>``.

    Gallery/docs belong to a product, so use the parent product's slug; top-
    level models (Product/News) use their own slug.
    """
    owner = getattr(instance, 'product', None) or instance
    base = getattr(owner, 'slug', None) or getattr(owner, 'pk', None) or 'item'
    name, ext = os.path.splitext(filename)
    safe = slugify(name) or 'file'
    return f'{subdir}/{base}/{safe}{ext.lower()}'


def product_cover_upload_to(instance, filename):
    return _path_for(instance, filename, 'products/covers')


def product_gallery_upload_to(instance, filename):
    return _path_for(instance, filename, 'products/gallery')


def product_doc_upload_to(instance, filename):
    return _path_for(instance, filename, 'products/docs')


def news_cover_upload_to(instance, filename):
    return _path_for(instance, filename, 'news/covers')


# --------------------------------------------------------------------------- #
# Product catalogue
# --------------------------------------------------------------------------- #
class ProductCategory(models.Model):
    """A product line, e.g. ``按产品线分``. Groups related products together."""

    name = models.CharField('名称', max_length=100, unique=True)
    slug = models.SlugField('URL标识', max_length=120, unique=True)
    summary = models.CharField('简述', max_length=200, blank=True)
    order = models.PositiveIntegerField('排序', default=0)
    is_visible = models.BooleanField('显示', default=True)

    class Meta:
        verbose_name = '产品分类'
        verbose_name_plural = '产品分类'
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse('product_list') + f'?cat={self.slug}'


class Product(models.Model):
    """A single product (kit, board, or platform) shown on the site."""

    category = models.ForeignKey(
        ProductCategory, on_delete=models.PROTECT,
        related_name='products', verbose_name='分类', null=True, blank=True,
    )
    name = models.CharField('名称', max_length=150)
    code = models.CharField('型号', max_length=80, blank=True,
                           help_text='产品型号，例如 AY-Smart Car')
    slug = models.SlugField('URL标识', max_length=160, unique=True)
    tagline = models.CharField('一句话卖点', max_length=200, blank=True)
    cover = models.ImageField(
        '封面图', upload_to=product_cover_upload_to,
        blank=True, help_text='列表与详情页主图，建议 1600x1200。',
    )
    summary = models.TextField('简介', blank=True,
                               help_text='卡片上展示的简短描述。')
    description = models.TextField('详细介绍', blank=True,
                                   help_text='支持 HTML，详情页正文。')
    specifications = models.TextField('规格参数', blank=True,
                                      help_text='一行一项，用 | 分隔列。')
    featured = models.BooleanField('首页推荐', default=False)
    order = models.PositiveIntegerField('排序', default=0)
    is_published = models.BooleanField('发布', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '产品'
        verbose_name_plural = '产品'
        ordering = ['order', '-created_at']

    def __str__(self) -> str:
        return f'{self.name} ({self.code})' if self.code else self.name

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})


class ProductImage(models.Model):
    """Extra gallery images for a product's detail page."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='images', verbose_name='所属产品',
    )
    image = models.ImageField(
        '图片', upload_to=product_gallery_upload_to,
    )
    caption = models.CharField('说明', max_length=200, blank=True)
    order = models.PositiveIntegerField('排序', default=0)

    class Meta:
        verbose_name = '产品图片'
        verbose_name_plural = '产品图片'
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return self.caption or f'{self.product.name} 图片'


class ProductDocument(models.Model):
    """A downloadable file attached to a product (guide, sample code, etc.).

    Uses FileField so arbitrary types — PDFs, ZIP archives, firmware — are
    served straight from the media store and renameable from the admin.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='documents', verbose_name='所属产品',
    )
    title = models.CharField('文件标题', max_length=200)
    file = models.FileField(
        '文件', upload_to=product_doc_upload_to,
        help_text='支持 PDF、ZIP、BIN 等任意格式。',
    )
    size_hint = models.CharField('文件大小标注', max_length=40, blank=True,
                                 help_text='可选，例如「3 MB」。')
    published_at = models.DateField('发布日期', null=True, blank=True)
    order = models.PositiveIntegerField('排序', default=0)

    class Meta:
        verbose_name = '产品资料'
        verbose_name_plural = '产品资料'
        ordering = ['order', '-published_at']

    def __str__(self) -> str:
        return self.title

    def file_size_label(self) -> str:
        """Human-readable size derived from the stored file when available."""
        if self.size_hint:
            return self.size_hint
        try:
            bytes_ = self.file.size
        except (OSError, ValueError):
            return ''
        for unit in ('B', 'KB', 'MB', 'GB'):
            if bytes_ < 1024:
                return f'{bytes_:.0f} {unit}' if unit == 'B' else f'{bytes_:.1f} {unit}'
            bytes_ /= 1024
        return f'{bytes_:.1f} TB'


class ProductExperiment(models.Model):
    """One row of the experiment list shown on a product detail page."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='experiments', verbose_name='所属产品',
    )
    title = models.CharField('实验名称', max_length=200)
    order = models.PositiveIntegerField('顺序', default=0)

    class Meta:
        verbose_name = '实验列表项'
        verbose_name_plural = '实验列表项'
        ordering = ['order', 'id']
        unique_together = [('product', 'order')]

    def __str__(self) -> str:
        return self.title


# --------------------------------------------------------------------------- #
# News & articles
# --------------------------------------------------------------------------- #
class NewsCategory(models.Model):
    """``企业动态`` or ``行业新闻``."""

    name = models.CharField('名称', max_length=80, unique=True)
    slug = models.SlugField('URL标识', max_length=100, unique=True)
    order = models.PositiveIntegerField('排序', default=0)

    class Meta:
        verbose_name = '新闻分类'
        verbose_name_plural = '新闻分类'
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse('news_list') + f'?cat={self.slug}'


class News(models.Model):
    """A news article. The forum has been dropped per the rebuild brief."""

    category = models.ForeignKey(
        NewsCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='articles', verbose_name='分类',
    )
    title = models.CharField('标题', max_length=200)
    slug = models.SlugField('URL标识', max_length=220, unique=True)
    cover = models.ImageField(
        '封面图', upload_to=news_cover_upload_to, blank=True,
    )
    excerpt = models.CharField('摘要', max_length=300, blank=True)
    body = models.TextField('正文', help_text='支持 HTML。')
    published_at = models.DateField('发布日期', null=True, blank=True)
    is_published = models.BooleanField('发布', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '新闻'
        verbose_name_plural = '新闻'
        ordering = ['-published_at', '-created_at']

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self):
        return reverse('news_detail', kwargs={'slug': self.slug})

    def clean(self):
        # Slugs are required to render detail URLs — guarantee one exists.
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        if News.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            raise ValidationError({'slug': '该 URL 标识已存在，请换一个。'})


# --------------------------------------------------------------------------- #
# Site-wide settings — a single-row table for hero copy, contact details, etc.
# --------------------------------------------------------------------------- #
class SiteSetting(models.Model):
    """Singleton: the first (and only) row powers the global site config."""

    company_name = models.CharField('公司名称', max_length=120,
                                    default='艾研信息')
    company_name_en = models.CharField('英文名称', max_length=120, blank=True,
                                       default='AiYan Information')
    tagline = models.CharField('品牌标语', max_length=200, blank=True,
                               default='为高校电子工程教育提供创新实验平台')
    logo = models.ImageField('Logo', upload_to='site/', blank=True)

    hero_title = models.CharField('首页主标题', max_length=200,
                                  default='让工程教育，回归动手实践')
    hero_subtitle = models.TextField('首页副标题',
                                      default='从单片机到物联网，从电源拓扑到智能小车——'
                                              '为高校实验室打造的模块化教学套件。')
    hero_image = models.ImageField('首页主视觉', upload_to='site/', blank=True,
                                   help_text='可选，首页英雄区背景图。')

    about_title = models.CharField('关于-标题', max_length=200, blank=True)
    about_body = models.TextField('关于-正文', blank=True,
                                   help_text='支持 HTML。')

    contact_address = models.CharField('地址', max_length=200, blank=True)
    contact_phone = models.CharField('电话', max_length=60, blank=True)
    contact_email = models.EmailField('邮箱', blank=True)
    contact_wechat = models.CharField('微信公众号', max_length=100, blank=True)
    contact_icp = models.CharField('备案号', max_length=100, blank=True)

    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '站点设置'
        verbose_name_plural = '站点设置'

    def __str__(self) -> str:
        return self.company_name

    @classmethod
    def get(cls):
        """Return the single canonical row, creating it lazily if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
