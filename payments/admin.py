from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display    = [
        'id', 'order', 'method', 'formatted_amount',
        'colored_status', 'transaction_id', 'created_at'
    ]
    list_filter     = ['method', 'status']
    search_fields   = ['order__id', 'transaction_id', 'order__user__email']
    readonly_fields = ['gateway_response', 'created_at', 'updated_at']

    def formatted_amount(self, obj):
        return f"Rs. {obj.amount:,.0f}"
    formatted_amount.short_description = 'Amount'

    def colored_status(self, obj):
        colors = {
            'pending':  '#f59e0b',
            'success':  '#10b981',
            'failed':   '#ef4444',
            'refunded': '#6366f1',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display()
        )
    colored_status.short_description = 'Status'

    # Optimized queryset
    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('order', 'order__user')
        )