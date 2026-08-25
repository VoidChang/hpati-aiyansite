"""
Admin configuration for the AiYan website.

Optimised so a content editor can manage products, news and site copy without
touching code. FileField/ImageField assets upload inline and are shown with
direct media links for quick review.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    News, NewsCategory, Product, ProductCategory, ProductDocument,
    ProductExperiment, ProductImage, SiteSetting,
)


# --------------------------------------------------------------------------- #
# Site settings — singleton, hide the list view.
# --------------------------------------------------------------------------- #
@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('品牌'), {'fields': ('company_name', 'company_name_en', 'tagline', 'logo')}),
        (_('首页主视觉'), {'fields': ('hero_title', 'hero_subtitle', 'hero_image')}),
        (_('关于我们'), {'fields': ('about_title', 'about_body')}),
        (_('联系方式'), {'fields': (
            'contact_address', 'contact_phone', 'contact_email',
            'contact_wechat', 'contact_icp',
        )}),
    )

    def has_add_permission(self, request):
        # Only ever one row — disable adding.
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.none() if not qs.exists() else qs

    def changelist_view(self, request, extra_context=None):
        # Auto-redirect to the single object's edit page.
        obj = SiteSetting.get()
        return self.change_view(request, str(obj.pk), extra_context)


# --------------------------------------------------------------------------- #
# Products
# --------------------------------------------------------------------------- #
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('preview',)
    fields = ('image', 'caption', 'order', 'preview')

    def preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height:120px;border-radius:6px;" />',
                obj.image.url,
            )
        return '—'
    preview.short_description = '预览'


class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 1
    fields = ('title', 'file', 'size_hint', 'published_at', 'order')
    readonly_fields = ()


class ProductExperimentInline(admin.TabularInline):
    model = ProductExperiment
    extra = 1
    fields = ('title', 'order')


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_visible', 'product_count')
    list_editable = ('order', 'is_visible')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    @admin.display(description='产品数')
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'featured', 'is_published', 'order', 'updated_at')
    list_editable = ('order', 'featured', 'is_published')
    list_filter = ('category', 'is_published', 'featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'code', 'tagline')
    readonly_fields = ('created_at', 'updated_at', 'cover_preview')
    fieldsets = (
        (_('基本信息'), {'fields': ('name', 'code', 'slug', 'category')}),
        (_('展示'), {'fields': ('tagline', 'cover', 'cover_preview', 'summary', 'description')}),
        (_('规格'), {'fields': ('specifications',)}),
        (_('发布'), {'fields': ('featured', 'is_published', 'order',
                               'created_at', 'updated_at')}),
    )
    inlines = [ProductImageInline, ProductDocumentInline, ProductExperimentInline]

    def cover_preview(self, obj):
        if obj and obj.cover:
            return format_html(
                '<img src="{}" style="max-height:140px;border-radius:8px;" />',
                obj.cover.url,
            )
        return '—'
    cover_preview.short_description = '封面预览'


# --------------------------------------------------------------------------- #
# News
# --------------------------------------------------------------------------- #
@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'article_count')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='文章数')
    def article_count(self, obj):
        return obj.articles.count()


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'published_at', 'is_published', 'updated_at')
    list_editable = ('is_published',)
    list_filter = ('category', 'is_published', 'published_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'excerpt')
    readonly_fields = ('created_at', 'updated_at', 'cover_preview')
    fieldsets = (
        (_('基本信息'), {'fields': ('title', 'slug', 'category', 'is_published')}),
        (_('封面'), {'fields': ('cover', 'cover_preview')}),
        (_('正文'), {'fields': ('excerpt', 'body')}),
        (_('时间'), {'fields': ('published_at', 'created_at', 'updated_at')}),
    )

    def cover_preview(self, obj):
        if obj and obj.cover:
            return format_html(
                '<img src="{}" style="max-height:140px;border-radius:8px;" />',
                obj.cover.url,
            )
        return '—'
    cover_preview.short_description = '封面预览'
