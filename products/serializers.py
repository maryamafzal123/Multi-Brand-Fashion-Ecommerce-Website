from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'image', 'product_count']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ['id', 'image', 'is_primary', 'order']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductVariant
        fields = ['id', 'size', 'color', 'stock', 'extra_price']


class ProductListSerializer(serializers.ModelSerializer):
    category         = CategorySerializer(read_only=True)
    primary_image    = serializers.SerializerMethodField()
    discount_percent = serializers.ReadOnlyField()
    in_stock         = serializers.ReadOnlyField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'category',
            'price', 'old_price', 'discount_percent',
            'age_range', 'gender', 'is_featured',
            'in_stock', 'stock', 'primary_image',
        ]

    def get_primary_image(self, obj):
        images = obj.images.all()
        primary = next((img for img in images if img.is_primary), None)
        img = primary or (images[0] if images else None)
        if img:
            request = self.context.get('request')
            return request.build_absolute_uri(img.image.url) if request else img.image.url
        return None


class ProductDetailSerializer(ProductListSerializer):
    images   = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            'description', 'stock', 'images',
            'variants', 'created_at',
        ]


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = [
            'name', 'slug', 'category', 'description',
            'price', 'old_price', 'stock', 'age_range',
            'gender', 'is_featured', 'is_active',
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than 0.')
        return value

    def validate(self, data):
        old_price = data.get('old_price')
        price     = data.get('price')
        if old_price and old_price <= price:
            raise serializers.ValidationError(
                'Old price must be greater than current price.'
            )
        return data