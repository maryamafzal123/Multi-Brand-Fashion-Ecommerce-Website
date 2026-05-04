from django.core.mail import get_connection, EmailMessage
from django.conf import settings


def send_with_timeout(subject, message, from_email, recipient_list):
    try:
        connection = get_connection(timeout=10)
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
            connection=connection,
        )
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Email error: {e}")


def send_order_placed_admin(order):
    items_text = '\n'.join([
        f"  - {item.name} x{item.quantity} = Rs. {item.subtotal}"
        for item in order.items.all()
    ])

    if order.user:
        customer_name = order.user.full_name
        customer_email = order.user.email
        customer_phone = order.user.phone or 'Not provided'
    else:
        customer_name = order.guest_name
        customer_email = order.guest_email
        customer_phone = order.guest_phone or 'Not provided'

    message = f"""
New Order Received! 🛍️

Order {order.order_number}
Customer: {customer_name}
Email: {customer_email}
Phone: {customer_phone}

Items:
{items_text}

Subtotal: Rs. {order.subtotal}
Delivery: Rs. {order.delivery_charge}
Total: Rs. {order.total}

Payment Method: {order.payment_method.upper()}
Payment Status: {order.payment_status.upper()}

Order Date: {order.created_at.strftime('%d %B %Y, %I:%M %p')}
    """.strip()

    send_with_timeout(
        subject=f'New Order {order.order_number} — Brand Bazar by Mirsa',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
    )


def send_order_confirmation_customer(order):
    items_text = '\n'.join([
        f"  - {item.name} x{item.quantity} = Rs. {item.subtotal}"
        for item in order.items.all()
    ])

    if order.user:
        customer_name = order.user.full_name
        customer_email = order.user.email
    else:
        customer_name = order.guest_name
        customer_email = order.guest_email

    message = f"""
Hi {customer_name}! 🎉

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

Need help? Contact us on WhatsApp:
+92 333 2742727

Thank you for choosing Brand Bazar by Mirsa! ✨

— Brand Bazar by Mirsa Team
    """.strip()

    send_with_timeout(
        subject=f'Order {order.order_number} Confirmed — Brand Bazar by Mirsa',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[customer_email],
    )


def send_order_shipped_customer(order):
    if order.user:
        customer_name = order.user.full_name
        customer_email = order.user.email
    else:
        customer_name = order.guest_name
        customer_email = order.guest_email

    message = f"""
Hi {customer_name}! 🚚

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
+92 333 2742727

Thank you for shopping with us! ✨

— Brand Bazar by Mirsa Team
    """.strip()

    send_with_timeout(
        subject=f'Order {order.order_number} Shipped — Brand Bazar by Mirsa',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[customer_email],
    )


def send_order_cancelled_customer(order):
    if order.user:
        customer_name = order.user.full_name
        customer_email = order.user.email
    else:
        customer_name = order.guest_name
        customer_email = order.guest_email

    message = f"""
Hi {customer_name},

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
+92 333 2742727

We hope to serve you again soon!

— Brand Bazar by Mirsa Team
    """.strip()

    send_with_timeout(
        subject=f'Order {order.order_number} Cancelled — Brand Bazar by Mirsa',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[customer_email],
    )