"""URL routes for the public website."""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('news/', views.NewsListView.as_view(), name='news_list'),
    path('news/<slug:slug>/', views.NewsDetailView.as_view(), name='news_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]

handler404 = 'website.views.custom_404'
