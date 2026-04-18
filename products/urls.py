from django.urls import path
from . import views

urlpatterns = [
    path('categories/',      views.CategoryListView.as_view(),    name='categories'),
    path('featured/',        views.FeaturedProductsView.as_view(), name='featured_products'),
    path('',                 views.ProductListView.as_view(),     name='products'),
    path('<slug:slug>/',     views.ProductDetailView.as_view(),   name='product_detail'),
]