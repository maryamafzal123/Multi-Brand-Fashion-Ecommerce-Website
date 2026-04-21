from django.db import models
from users.models import User, Address
from products.models import Product, ProductVariant


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cod',  'Cash on Delivery'),
        ('bank', 'Bank Transfer'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders',
        db_index=True
    )
    shipping_address = models.ForeignKey(
        Address, on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True
    )

    # ── Guest fields ──
    guest_name    = models.CharField(max_length=200, blank=True)
    guest_email   = models.EmailField(blank=True)
    guest_phone   = models.CharField(max_length=20, blank=True)
    guest_address = models.TextField(blank=True)

    status           = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending', db_index=True
    )
    payment_method   = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES,
        db_index=True
    )
    payment_status   = models.CharField(
        max_length=20, default='unpaid',
        db_index=True
    )
    subtotal         = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_charge  = models.DecimalField(max_digits=8, decimal_places=2, default=200)
    total            = models.DecimalField(max_digits=10, decimal_places=2)
    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'payment_status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        name = self.guest_name or (self.user.full_name if self.user else 'Unknown')
        return f"Order #{self.id} — {name}"

    @property
    def order_number(self):
        return f"BB-{str(self.id).zfill(4)}"

    def calculate_total(self):
        from django.db.models import Sum, F, ExpressionWrapper, DecimalField
        result = self.items.annotate(
            line_total=ExpressionWrapper(
                F('price') * F('quantity'),
                output_field=DecimalField()
            )
        ).aggregate(subtotal=Sum('line_total'))

        self.subtotal = result['subtotal'] or 0
        self.delivery_charge = 0 if self.subtotal >= 3000 else 200
        self.total    = self.subtotal + self.delivery_charge
        self.save(update_fields=['subtotal', 'delivery_charge', 'total'])


class OrderItem(models.Model):
    order    = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='items', db_index=True
    )
    product  = models.ForeignKey(
        Product, on_delete=models.SET_NULL,
        null=True, db_index=True
    )
    variant  = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    name     = models.CharField(max_length=200)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=['order', 'product']),
        ]

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.name}"