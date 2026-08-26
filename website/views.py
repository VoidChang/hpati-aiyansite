"""Public views for the AiYan website."""
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .models import (
    News, NewsCategory, Product, ProductCategory, Resource, SiteSetting,
)


# --------------------------------------------------------------------------- #
# Home
# --------------------------------------------------------------------------- #
def home(request):
    featured = Product.objects.filter(is_published=True, featured=True).order_by('order', '-created_at')
    latest_news = News.objects.filter(is_published=True).order_by('-published_at', '-created_at')[:6]
    categories = ProductCategory.objects.filter(is_visible=True)
    return render(request, 'home.html', {
        'featured_products': featured,
        'latest_news': latest_news,
        'categories': categories,
    })


# --------------------------------------------------------------------------- #
# Products
# --------------------------------------------------------------------------- #
class ProductListView(ListView):
    template_name = 'product_list.html'
    paginate_by = 9
    context_object_name = 'products'

    def get_queryset(self):
        qs = Product.objects.filter(is_published=True).order_by('order', '-created_at')
        cat = self.request.GET.get('cat')
        if cat:
            qs = qs.filter(category__slug=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = ProductCategory.objects.filter(is_visible=True)
        ctx['active_cat'] = self.request.GET.get('cat', '')
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object
        ctx['related'] = Product.objects.filter(
            is_published=True, category=product.category,
        ).exclude(pk=product.pk)[:3]
        ctx['experiments'] = product.experiments.all()
        ctx['documents'] = product.documents.all()
        return ctx


# --------------------------------------------------------------------------- #
# News
# --------------------------------------------------------------------------- #
class NewsListView(ListView):
    template_name = 'news_list.html'
    paginate_by = 10
    context_object_name = 'news'

    def get_queryset(self):
        qs = News.objects.filter(is_published=True).order_by('-published_at', '-created_at')
        cat = self.request.GET.get('cat')
        if cat:
            qs = qs.filter(category__slug=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = NewsCategory.objects.all()
        ctx['active_cat'] = self.request.GET.get('cat', '')
        return ctx


class NewsDetailView(DetailView):
    model = News
    template_name = 'news_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return News.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['related'] = News.objects.filter(
            is_published=True, category=self.object.category,
        ).exclude(pk=self.object.pk)[:3]
        return ctx


# --------------------------------------------------------------------------- #
# Static pages
# --------------------------------------------------------------------------- #
def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


# --------------------------------------------------------------------------- #
# Resource centre
# --------------------------------------------------------------------------- #
class ResourceListView(ListView):
    template_name = 'resource_list.html'
    paginate_by = 20
    context_object_name = 'resources'

    def get_queryset(self):
        qs = Resource.objects.filter(is_published=True).order_by(
            'category', 'order', '-created_at',
        )
        cat = self.request.GET.get('cat')
        if cat and cat in dict(Resource.CATEGORY_CHOICES):
            qs = qs.filter(category=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Resource.CATEGORY_CHOICES
        ctx['active_cat'] = self.request.GET.get('cat', '')
        return ctx


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)
