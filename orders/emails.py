from django.core.mail import send_mail
from django.conf import settings


def send_order_placed_admin(order):
    """Email to admin when new order is placed."""
    items_text = '\n'.join([
        f"  - {item.name} x{item.quantity} = Rs. {item.subtotal}"
        for item in order.items.all()
    ])

    message = f"""
New Order Received! 🛍️

Order {order.order_number}
Customer: {order.user.full_name}
Email: {order.user.email}
Phone: {order.user.phone or 'Not provided'}

Items:
{items_text}

Subtotal: Rs. {order.subtotal}
Delivery: Rs. {order.delivery_charge}
Total: Rs. {order.total}

Payment Method: {order.payment_method.upper()}
Payment Status: {order.payment_status.upper()}

Order Date: {order.created_at.strftime('%d %B %Y, %I:%M %p')}
    """.strip()

    send_mail(
        subject=f'New Order {order.order_number} — Brand Bazar by Mirsa',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=True,
    )


def send_order_confirmation_customer(order):
    """Email to customer when order is placed."""
    items_text = '\n'.join([
        f"  - {item.name} x{item.quantity} = Rs. {item.subtotal}"
        for item in order.items.all()
    ])

    message = f"""
Hi {order.user.full_name}! 🎉

Thank you for shopping with Brand Bazar by Mirsa!

Your order has been confirmed and we are preparing it for you.

━━━━━━━━━━━━━━━━━━━━━━
ORDER DETAILS
━━━━━━━━━━━━━━━━━━━━━━

Order {order.order_number}
Date: {order.created_at.strftime('%d %B %Y')}

Items:
{items_text}

Subtotal:  Rs. {order.subtotal}
Delivery:  Rs. {order.delivery_charge}
Total:     Rs. {order.total}

Payment:   {order.payment_method.upper()}

━━━━━━━━━━━━━━━━━━━━━━

You can track your order status by logging into your account at:
http://localhost:3000/orders

Need help? Contact us on WhatsApp:
+92 333 6262574

Thank you for choosing Brand Bazar by Mirsa! ✨

— Brand Bazar by Mirsa Team
    """.strip()

    send_mail(
        subject=f'Order {order.order_number} Confirmed — Brand Bazar by Mirsa',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )


def send_order_shipped_customer(order):
    """Email to customer when order is shipped."""
    message = f"""
Hi {order.user.full_name}! 🚚

Great news! Your order {order.order_number} is on its way to you!

Your order has been shipped and will be delivered to you soon.

━━━━━━━━━━━━━━━━━━━━━━
ORDER SUMMARY
━━━━━━━━━━━━━━━━━━━━━━

Order {order.order_number}
Total: Rs. {order.total}
Payment: {order.payment_method.upper()}

━━━━━━━━━━━━━━━━━━━━━━

Need help? Contact us on WhatsApp:
+92 333 6262574

Thank you for shopping with us! ✨

— Brand Bazar by Mirsa Team
    """.strip()

    send_mail(
        subject=f'Order {order.order_number} Shipped — Brand Bazar by Mirsa',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )


def send_order_cancelled_customer(order):
    """Email to customer when order is cancelled."""
    message = f"""
Hi {order.user.full_name},

We're informing you that your order {order.order_number} has been cancelled.

━━━━━━━━━━━━━━━━━━━━━━
ORDER DETAILS
━━━━━━━━━━━━━━━━━━━━━━

Order {order.order_number}
Total: Rs. {order.total}
Payment: {order.payment_method.upper()}

━━━━━━━━━━━━━━━━━━━━━━

If you have any questions or did not request this cancellation,
please contact us immediately on WhatsApp:
+92 333 6262574

We hope to serve you again soon!

— Brand Bazar by Mirsa Team
    """.strip()

    send_mail(
        subject=f'Order {order.order_number} Cancelled — Brand Bazar by Mirsa',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )