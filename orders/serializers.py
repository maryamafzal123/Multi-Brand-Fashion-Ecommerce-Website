# import threading
from rest_framework import serializers
from django.db import transaction
from django.db.models import F
from .models import Order, OrderItem
from products.models import Product, ProductVariant
from .emails import send_order_placed_admin, send_order_confirmation_customer


class OrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity   = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError('Product not found or unavailable.')
        return value


class OrderCreateSerializer(serializers.Serializer):
    # Guest fields
    guest_name    = serializers.CharField(required=False, allow_blank=True)
    guest_email   = serializers.EmailField(required=False, allow_blank=True)
    guest_phone   = serializers.CharField(required=False, allow_blank=True)
    guest_address = serializers.CharField(required=False, allow_blank=True)

    payment_method = serializers.ChoiceField(choices=['cod', 'bank'])
    notes          = serializers.CharField(required=False, allow_blank=True)
    items          = OrderItemWriteSerializer(many=True)

    def validate(self, data):
        # Must have either guest info or authenticated user
        request = self.context.get('request')
        is_authenticated = request and request.user and request.user.is_authenticated

        if not is_authenticated:
            if not data.get('guest_name'):
                raise serializers.ValidationError({'guest_name': 'Name is required.'})
            if not data.get('guest_email'):
                raise serializers.ValidationError({'guest_email': 'Email is required.'})
            if not data.get('guest_phone'):
                raise serializers.ValidationError({'guest_phone': 'Phone is required.'})
            if not data.get('guest_address'):
                raise serializers.ValidationError({'guest_address': 'Address is required.'})
        return data

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError('Order must have at least one item.')
        for item in items:
            product_id = item['product_id']
            qty        = item['quantity']
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                raise serializers.ValidationError('Product not found or unavailable.')
            if product.stock < qty:
                raise serializers.ValidationError(
                    f'Only {product.stock} left in stock for "{product.name}".'
                )
        return items

    @transaction.atomic
    def create(self, validated_data):
        request    = self.context.get('request')
        items_data = validated_data.pop('items')
        is_authenticated = request and request.user and request.user.is_authenticated

        # Lock products
        product_ids  = [item['product_id'] for item in items_data]
        products     = Product.objects.select_for_update(of=('self',)).filter(
            id__in=product_ids
        ).select_related('category')
        products_map = {p.id: p for p in products}

        # Lock variants
        variant_ids  = [item['variant_id'] for item in items_data if item.get('variant_id')]
        variants_map = {}
        if variant_ids:
            variants     = ProductVariant.objects.select_for_update(of=('self',)).filter(id__in=variant_ids)
            variants_map = {v.id: v for v in variants}

        # Re-validate stock
        for item_data in items_data:
            product    = products_map[item_data['product_id']]
            variant_id = item_data.get('variant_id')
            qty        = item_data['quantity']

            if variant_id:
                variant = variants_map.get(variant_id)
                if not variant or variant.stock < qty:
                    available = variant.stock if variant else 0
                    raise serializers.ValidationError(
                        f'Sorry! Only {available} left for "{product.name}".'
                    )
            else:
                if product.stock < qty:
                    raise serializers.ValidationError(
                        f'Sorry! Only {product.stock} left for "{product.name}".'
                    )

        # Create order
        order = Order.objects.create(
            user=request.user if is_authenticated else None,
            guest_name=validated_data.get('guest_name', ''),
            guest_email=validated_data.get('guest_email', ''),
            guest_phone=validated_data.get('guest_phone', ''),
            guest_address=validated_data.get('guest_address', ''),
            payment_method=validated_data['payment_method'],
            notes=validated_data.get('notes', ''),
            subtotal=0,
            total=0,
        )

        # Create order items
        order_items = []
        for item_data in items_data:
            product = products_map[item_data['product_id']]
            variant = variants_map.get(item_data.get('variant_id'))
            price   = product.price + (variant.extra_price if variant else 0)

            order_items.append(OrderItem(
                order=order,
                product=product,
                variant=variant,
                name=product.name,
                price=price,
                quantity=item_data['quantity'],
            ))

        OrderItem.objects.bulk_create(order_items)

        # Deduct stock
        for item_data in items_data:
            product = products_map[item_data['product_id']]
            variant = variants_map.get(item_data.get('variant_id'))
            qty     = item_data['quantity']

            if variant:
                ProductVariant.objects.filter(id=variant.id).update(stock=F('stock') - qty)
            else:
                Product.objects.filter(id=product.id).update(stock=F('stock') - qty)

        order.calculate_total()
        transaction.on_commit(lambda: send_order_placed_admin(order))
        transaction.on_commit(lambda: send_order_confirmation_customer(order))
        return order


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model  = OrderItem
        fields = ['id', 'name', 'price', 'quantity', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items        = OrderItemSerializer(many=True, read_only=True)
    order_number = serializers.ReadOnlyField()

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'payment_method', 'payment_status',
            'subtotal', 'delivery_charge', 'total', 'guest_name', 'guest_email',
            'guest_phone', 'guest_address', 'notes', 'items', 'created_at',
        ]