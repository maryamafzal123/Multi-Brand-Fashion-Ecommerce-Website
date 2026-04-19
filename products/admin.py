from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductVariant


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_primary', 'order', 'preview', 'delete_image']
    readonly_fields = ['preview', 'delete_image']
    can_delete = True  # ← allows deleting individual images

    def preview(self, obj):
        if not obj.image:
            return '—'
        url = obj.image.url
        name = url.lower()
        if any(name.endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv']):
            return format_html(
                '<video width="80" height="60" controls '
                'style="object-fit:cover; border-radius:4px;">'
                '<source src="{}" />Your browser does not support video.</video>',
                url
            )
        return format_html(
            '<img src="{}" width="60" height="60" '
            'style="object-fit:cover; border-radius:4px;" />',
            url
        )
    preview.short_description = 'Preview'

    def delete_image(self, obj):
        if not obj.pk:
            return '—'
        return format_html(
            '<a href="/admin/products/productimage/{}/delete/" '
            'style="color:red; font-weight:bold;" '
            'onclick="return confirm(\'Delete this image only?\')">🗑 Delete</a>',
            obj.pk
        )
    delete_image.short_description = 'Delete Image'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['size', 'color', 'stock', 'extra_price']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price', 'old_price',
        'stock', 'age_range', 'gender',
        'is_featured', 'is_active', 'created_at'
    ]
    list_filter = ['category', 'gender', 'is_featured', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock', 'is_featured', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline, ProductVariantInline]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('category')
            .prefetch_related('images', 'variants')
        )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'is_primary', 'order', 'preview']
    list_filter = ['is_primary', 'product']
    readonly_fields = ['preview']

    def preview(self, obj):
        if not obj.image:
            return '—'
        url = obj.image.url
        name = url.lower()
        if any(name.endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv']):
            return format_html(
                '<video width="120" height="80" controls>'
                '<source src="{}" /></video>',
                url
            )
        return format_html(
            '<img src="{}" width="80" height="80" style="object-fit:cover;" />',
            url
        )
    preview.short_description = 'Preview'