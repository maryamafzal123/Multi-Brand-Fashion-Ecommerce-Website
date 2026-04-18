from django.db import models
from orders.models import Order


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('success',  'Success'),
        ('failed',   'Failed'),
        ('refunded', 'Refunded'),
    ]
    METHOD_CHOICES = [
        ('cod',       'Cash on Delivery'),
        ('bank', 'Bank Transfer'),
    ]

    order            = models.OneToOneField(
        Order, on_delete=models.CASCADE,
        related_name='payment', db_index=True
    )
    method           = models.CharField(
        max_length=20, choices=METHOD_CHOICES,
        db_index=True
    )
    amount           = models.DecimalField(max_digits=10, decimal_places=2)
    status           = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending', db_index=True
    )
    transaction_id   = models.CharField(max_length=200, blank=True, db_index=True)
    gateway_ref      = models.CharField(max_length=200, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['status', 'method']),
            models.Index(fields=['transaction_id']),
        ]

    def __str__(self):
        return f"Payment #{self.id} — {self.method} — {self.status}"

    def mark_success(self, transaction_id, gateway_response=None):
        """
        Marks payment as success and updates order status.
        Uses update_fields for minimal DB writes.
        """
        from django.db import transaction
        with transaction.atomic():
            self.status         = 'success'
            self.transaction_id = transaction_id
            if gateway_response:
                self.gateway_response = gateway_response
            self.save(update_fields=['status', 'transaction_id', 'gateway_response', 'updated_at'])

            # Update order in same transaction
            self.order.payment_status = 'paid'
            self.order.status         = 'confirmed'
            self.order.save(update_fields=['payment_status', 'status'])

    def mark_failed(self, gateway_response=None):
        if gateway_response:
            self.gateway_response = gateway_response
        self.status = 'failed'
        self.save(update_fields=['status', 'gateway_response', 'updated_at'])