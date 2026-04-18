from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem
from .emails import send_order_shipped_customer, send_order_cancelled_customer


class OrderItemInline(admin.TabularInline):
    model           = OrderItem
    extra           = 0
    readonly_fields = ['name', 'price', 'quantity', 'subtotal']
    can_delete      = False

    def subtotal(self, obj):
        return f"Rs. {obj.subtotal:,.0f}"
    subtotal.short_description = 'Subtotal'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = [
        'get_order_number', 'user', 'status', 'payment_method',
        'payment_status', 'formatted_total', 'created_at'
    ]
    list_filter     = ['status', 'payment_method', 'payment_status']
    search_fields   = ['user__email', 'user__full_name', 'id']
    list_editable   = ['status']
    readonly_fields = ['subtotal', 'total', 'created_at', 'updated_at']
    inlines         = [OrderItemInline]

    def get_order_number(self, obj):
        return obj.order_number
    get_order_number.short_description = 'Order Number'

    def formatted_total(self, obj):
        return format_html('<strong>Rs. {}</strong>', f"{float(obj.total):,.0f}")
    formatted_total.short_description = 'Total'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'status' in form.base_fields:
            form.base_fields['status'].choices = [
                ('pending',   'Pending'),
                ('shipped',   'Shipped'),
                ('delivered', 'Delivered'),
                ('cancelled', 'Cancelled'),
            ]
        return form

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('user', 'shipping_address')
            .prefetch_related('items')
        )

    def save_model(self, request, obj, form, change):
        if change:
            old        = Order.objects.get(pk=obj.pk)
            old_status = old.status
            super().save_model(request, obj, form, change)

            if obj.status != old_status:
                order = Order.objects.select_related('user').prefetch_related('items').get(pk=obj.pk)
                if obj.status == 'shipped':
                    send_order_shipped_customer(order)
                elif obj.status == 'cancelled':
                    send_order_cancelled_customer(order)
        else:
            super().save_model(request, obj, form, change)