from rest_framework import generics, filters, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ProductImage, ProductVariant
from .serializers import (
    CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductWriteSerializer
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Read access to everyone.
    Write access to admin users only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


def get_optimized_product_queryset():
    """
    Reusable base queryset with all joins and prefetches.
    Prevents N+1 queries across all product views.
    """
    return (
        Product.objects
        .filter(is_active=True)
        .select_related('category')
        .prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.order_by('order')
            ),
            Prefetch(
                'variants',
                queryset=ProductVariant.objects.order_by('size')
            ),
        )
    )


class CategoryListView(generics.ListCreateAPIView):
    queryset           = Category.objects.prefetch_related('products').all()
    serializer_class   = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['name', 'description']
    ordering_fields    = ['price', 'created_at']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs = get_optimized_product_queryset()

        # Filters from query params
        category = self.request.query_params.get('category')
        gender   = self.request.query_params.get('gender')
        age      = self.request.query_params.get('age_range')
        featured = self.request.query_params.get('featured')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if category:  qs = qs.filter(category__slug=category)
        if gender:    qs = qs.filter(gender=gender)
        if age:       qs = qs.filter(age_range=age)
        if featured:  qs = qs.filter(is_featured=True)
        if min_price: qs = qs.filter(price__gte=min_price)
        if max_price: qs = qs.filter(price__lte=max_price)

        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductWriteSerializer
        return ProductListSerializer


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    lookup_field       = 'slug'

    def get_queryset(self):
        return get_optimized_product_queryset()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductDetailSerializer
        return ProductWriteSerializer

    def destroy(self, request, *args, **kwargs):
        # Soft delete — never hard delete products
        product = self.get_object()
        product.is_active = False
        product.save(update_fields=['is_active'])
        return Response(
            {'message': 'Product deactivated successfully.'},
            status=status.HTTP_200_OK
        )


class FeaturedProductsView(generics.ListAPIView):
    """Separate endpoint for homepage featured products."""
    serializer_class   = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return get_optimized_product_queryset().filter(is_featured=True)[:8]