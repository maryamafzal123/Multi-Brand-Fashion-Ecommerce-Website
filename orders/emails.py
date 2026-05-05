from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from products.models import ProductImage


def get_product_image(product):
    if not product:
        return None
    img = ProductImage.objects.filter(product=product, is_primary=True).first()
    if not img:
        img = ProductImage.objects.filter(product=product).first()
    return img.image.url if img else None


def send_order_placed_admin(order):
    items_data = []
    for item in order.items.select_related('product', 'product__category', 'variant').all():
        image_url = get_product_image(item.product)
        category = item.product.category.name if item.product and item.product.category else ''
        variant_info = ''
        if item.variant:
            variant_info = f"{item.variant.size}{' / ' + item.variant.color if item.variant.color else ''}"
        product_url = f"https://brandbazarbymirsa.com/products/{item.product.slug}" if item.product else ''
        items_data.append({
            'name': item.name,
            'category': category,
            'variant': variant_info,
            'quantity': item.quantity,
            'price': item.subtotal,
            'image_url': image_url,
            'product_url': product_url,
        })

    if order.user:
        customer_name = order.user.full_name
        customer_email = order.user.email
        customer_phone = order.user.phone or 'Not provided'
    else:
        customer_name = order.guest_name
        customer_email = order.guest_email
        customer_phone = order.guest_phone or 'Not provided'

    items_html = ''
    for item in items_data:
        image_tag = f'<img src="{item["image_url"]}" width="80" height="80" style="object-fit:cover;border-radius:4px;" />' if item['image_url'] else '📦'
        variant_tag = f'<br><small style="color:#888;">Variant: {item["variant"]}</small>' if item['variant'] else ''
        items_html += f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #eee;width:100px;text-align:center;">{image_tag}</td>
            <td style="padding:10px;border-bottom:1px solid #eee;">
                <a href="{item['product_url']}" style="color:#b8960c;font-weight:bold;text-decoration:none;">{item['name']}</a>
                <br><small style="color:#888;">{item['category']}</small>
                {variant_tag}
                <br><small>Qty: {item['quantity']}</small>
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;font-weight:bold;">Rs. {item['price']}</td>
        </tr>
        """

    items_text = '\n'.join([
        f"  - {i['name']} ({i['category']}) {i['variant']} x{i['quantity']} = Rs. {i['price']}"
        for i in items_data
    ])

    plain_message = f"""
New Order Received!

Order {order.order_number}
Customer: {customer_name}
Email: {customer_email}
Phone: {customer_phone}

Items:
{items_text}

Subtotal: Rs. {order.subtotal}
Delivery: Rs. {order.delivery_charge}
Total: Rs. {order.total}

Payment: {order.payment_method.upper()}
Date: {order.created_at.strftime('%d %B %Y, %I:%M %p')}
    """.strip()

    html_message = f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <div style="background:#0a0a0a;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
            <h1 style="color:#b8960c;margin:0;font-size:24px;">BRAND BAZAR</h1>
            <p style="color:#fff;margin:5px 0;font-size:12px;letter-spacing:3px;">BY MIRSA</p>
        </div>
        <div style="background:#fff;padding:20px;border:1px solid #eee;">
            <h2 style="color:#111;">🛍️ New Order Received!</h2>
            <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
                <tr><td style="padding:5px;color:#888;">Order</td><td style="padding:5px;font-weight:bold;">{order.order_number}</td></tr>
                <tr><td style="padding:5px;color:#888;">Customer</td><td style="padding:5px;">{customer_name}</td></tr>
                <tr><td style="padding:5px;color:#888;">Email</td><td style="padding:5px;">{customer_email}</td></tr>
                <tr><td style="padding:5px;color:#888;">Phone</td><td style="padding:5px;">{customer_phone}</td></tr>
                <tr><td style="padding:5px;color:#888;">Payment</td><td style="padding:5px;">{order.payment_method.upper()}</td></tr>
                <tr><td style="padding:5px;color:#888;">Date</td><td style="padding:5px;">{order.created_at.strftime('%d %B %Y, %I:%M %p')}</td></tr>
            </table>

            <h3 style="color:#111;border-bottom:2px solid #b8960c;padding-bottom:8px;">Order Items</h3>
            <table style="width:100%;border-collapse:collapse;">
                {items_html}
            </table>

            <table style="width:100%;margin-top:20px;">
                <tr><td style="padding:5px;color:#888;">Subtotal</td><td style="padding:5px;text-align:right;">Rs. {order.subtotal}</td></tr>
                <tr><td style="padding:5px;color:#888;">Delivery</td><td style="padding:5px;text-align:right;">Rs. {order.delivery_charge}</td></tr>
                <tr style="font-size:18px;font-weight:bold;">
                    <td style="padding:10px 5px;color:#111;border-top:2px solid #b8960c;">Total</td>
                    <td style="padding:10px 5px;text-align:right;color:#b8960c;border-top:2px solid #b8960c;">Rs. {order.total}</td>
                </tr>
            </table>
        </div>
        <div style="background:#f5f5f5;padding:10px;text-align:center;font-size:12px;color:#888;border-radius:0 0 8px 8px;">
            Brand Bazar by Mirsa © 2026
        </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(
        subject=f'New Order {order.order_number} — Brand Bazar by Mirsa',
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_EMAIL],
    )
    msg.attach_alternative(html_message, "text/html")
    msg.send(fail_silently=True)


def send_order_confirmation_customer(order):
    items_data = []
    for item in order.items.select_related('product', 'product__category', 'variant').all():
        image_url = get_product_image(item.product)
        category = item.product.category.name if item.product and item.product.category else ''
        variant_info = ''
        if item.variant:
            variant_info = f"{item.variant.size}{' / ' + item.variant.color if item.variant.color else ''}"
        product_url = f"https://brandbazarbymirsa.com/products/{item.product.slug}" if item.product else ''
        items_data.append({
            'name': item.name,
            'category': category,
            'variant': variant_info,
            'quantity': item.quantity,
            'price': item.subtotal,
            'image_url': image_url,
            'product_url': product_url,
        })

    if order.user:
        customer_name = order.user.full_name
        customer_email = order.user.email
    else:
        customer_name = order.guest_name
        customer_email = order.guest_email

    items_html = ''
    for item in items_data:
        image_tag = f'<img src="{item["image_url"]}" width="80" height="80" style="object-fit:cover;border-radius:4px;" />' if item['image_url'] else '📦'
        variant_tag = f'<br><small style="color:#888;">Variant: {item["variant"]}</small>' if item['variant'] else ''
        items_html += f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #eee;width:100px;text-align:center;">{image_tag}</td>
            <td style="padding:10px;border-bottom:1px solid #eee;">
                <a href="{item['product_url']}" style="color:#b8960c;font-weight:bold;text-decoration:none;">{item['name']}</a>
                <br><small style="color:#888;">{item['category']}</small>
                {variant_tag}
                <br><small>Qty: {item['quantity']}</small>
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;font-weight:bold;">Rs. {item['price']}</td>
        </tr>
        """

    items_text = '\n'.join([
        f"  - {i['name']} ({i['category']}) x{i['quantity']} = Rs. {i['price']}"
        for i in items_data
    ])

    plain_message = f"""
Hi {customer_name}!

Thank you for shopping with Brand Bazar by Mirsa!
Your order has been confirmed.

Order {order.order_number}
Date: {order.created_at.strftime('%d %B %Y')}

Items:
{items_text}

Subtotal: Rs. {order.subtotal}
Delivery: Rs. {order.delivery_charge}
Total: Rs. {order.total}

Payment: {order.payment_method.upper()}

Need help? WhatsApp: +92 333 2742727
    """.strip()

    html_message = f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <div style="background:#0a0a0a;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
            <h1 style="color:#b8960c;margin:0;font-size:24px;">BRAND BAZAR</h1>
            <p style="color:#fff;margin:5px 0;font-size:12px;letter-spacing:3px;">BY MIRSA</p>
        </div>
        <div style="background:#fff;padding:20px;border:1px solid #eee;">
            <h2 style="color:#111;">🎉 Order Confirmed!</h2>
            <p style="color:#555;">Hi <strong>{customer_name}</strong>, thank you for shopping with us! Your order has been confirmed and we are preparing it for you.</p>

            <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
                <tr><td style="padding:5px;color:#888;">Order</td><td style="padding:5px;font-weight:bold;">{order.order_number}</td></tr>
                <tr><td style="padding:5px;color:#888;">Date</td><td style="padding:5px;">{order.created_at.strftime('%d %B %Y')}</td></tr>
                <tr><td style="padding:5px;color:#888;">Payment</td><td style="padding:5px;">{order.payment_method.upper()}</td></tr>
            </table>

            <h3 style="color:#111;border-bottom:2px solid #b8960c;padding-bottom:8px;">Your Items</h3>
            <table style="width:100%;border-collapse:collapse;">
                {items_html}
            </table>

            <table style="width:100%;margin-top:20px;">
                <tr><td style="padding:5px;color:#888;">Subtotal</td><td style="padding:5px;text-align:right;">Rs. {order.subtotal}</td></tr>
                <tr><td style="padding:5px;color:#888;">Delivery</td><td style="padding:5px;text-align:right;">Rs. {order.delivery_charge}</td></tr>
                <tr style="font-size:18px;font-weight:bold;">
                    <td style="padding:10px 5px;color:#111;border-top:2px solid #b8960c;">Total</td>
                    <td style="padding:10px 5px;text-align:right;color:#b8960c;border-top:2px solid #b8960c;">Rs. {order.total}</td>
                </tr>
            </table>

            <div style="margin-top:20px;padding:15px;background:#f9f9f9;border-radius:8px;text-align:center;">
                <p style="margin:0;color:#555;font-size:14px;">Need help? Contact us on WhatsApp</p>
                <a href="https://wa.me/923332742727" style="color:#25d366;font-weight:bold;font-size:16px;">+92 333 2742727</a>
            </div>
        </div>
        <div style="background:#f5f5f5;padding:10px;text-align:center;font-size:12px;color:#888;border-radius:0 0 8px 8px;">
            Brand Bazar by Mirsa © 2026 | <a href="https://brandbazarbymirsa.com" style="color:#b8960c;">brandbazarbymirsa.com</a>
        </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(
        subject=f'Order {order.order_number} Confirmed — Brand Bazar by Mirsa',
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[customer_email],
    )
    msg.attach_alternative(html_message, "text/html")
    msg.send(fail_silently=True)

def send_order_shipped_customer(order):
    items_data = []
    for item in order.items.select_related('product', 'product__category', 'variant').all():
        image_url = get_product_image(item.product)
        variant_info = ''
        if item.variant:
            variant_info = f"{item.variant.size}{' / ' + item.variant.color if item.variant.color else ''}"
        items_data.append({
            'name': item.name,
            'quantity': item.quantity,
            'price': item.subtotal,
            'image_url': image_url,
            'variant': variant_info,
        })

    if order.user:
        customer_name = order.user.full_name
        customer_email = order.user.email
    else:
        customer_name = order.guest_name
        customer_email = order.guest_email

    items_html = ''
    for item in items_data:
        image_tag = f'<img src="{item["image_url"]}" width="80" height="80" style="object-fit:cover;border-radius:4px;" />' if item['image_url'] else '📦'
        variant_tag = f'<br><small style="color:#888;">Variant: {item["variant"]}</small>' if item['variant'] else ''
        items_html += f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #eee;width:100px;text-align:center;">{image_tag}</td>
            <td style="padding:10px;border-bottom:1px solid #eee;">
                <strong>{item['name']}</strong>
                {variant_tag}
                <br><small>Qty: {item['quantity']}</small>
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;font-weight:bold;">Rs. {item['price']}</td>
        </tr>
        """

    plain_message = f"""
Hi {customer_name}!
Your order {order.order_number} has been shipped!
Total: Rs. {order.total}
Need help? WhatsApp: +92 333 2742727
    """.strip()

    html_message = f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <div style="background:#0a0a0a;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
            <h1 style="color:#b8960c;margin:0;font-size:24px;">BRAND BAZAR</h1>
            <p style="color:#fff;margin:5px 0;font-size:12px;letter-spacing:3px;">BY MIRSA</p>
        </div>
        <div style="background:#fff;padding:20px;border:1px solid #eee;">
            <h2 style="color:#111;">🚚 Your Order is on its Way!</h2>
            <p style="color:#555;">Hi <strong>{customer_name}</strong>, your order has been shipped and will be delivered soon.</p>

            <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
                <tr><td style="padding:5px;color:#888;">Order</td><td style="padding:5px;font-weight:bold;">{order.order_number}</td></tr>
                <tr><td style="padding:5px;color:#888;">Total</td><td style="padding:5px;color:#b8960c;font-weight:bold;">Rs. {order.total}</td></tr>
                <tr><td style="padding:5px;color:#888;">Payment</td><td style="padding:5px;">{order.payment_method.upper()}</td></tr>
            </table>

            <h3 style="color:#111;border-bottom:2px solid #b8960c;padding-bottom:8px;">Items Shipped</h3>
            <table style="width:100%;border-collapse:collapse;">
                {items_html}
            </table>

            <div style="margin-top:20px;padding:15px;background:#f0f9f0;border-radius:8px;text-align:center;border:1px solid #c3e6cb;">
                <p style="margin:0;color:#155724;font-size:14px;">📦 Expected delivery in 3-5 working days.</p>
            </div>

            <div style="margin-top:20px;padding:15px;background:#f9f9f9;border-radius:8px;text-align:center;">
                <p style="margin:0;color:#555;font-size:14px;">Need help? Contact us on WhatsApp</p>
                <a href="https://wa.me/923332742727" style="color:#25d366;font-weight:bold;font-size:16px;">+92 333 2742727</a>
            </div>
        </div>
        <div style="background:#f5f5f5;padding:10px;text-align:center;font-size:12px;color:#888;border-radius:0 0 8px 8px;">
            Brand Bazar by Mirsa © 2026 | <a href="https://brandbazarbymirsa.com" style="color:#b8960c;">brandbazarbymirsa.com</a>
        </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(
        subject=f'Order {order.order_number} Shipped — Brand Bazar by Mirsa',
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[customer_email],
    )
    msg.attach_alternative(html_message, "text/html")
    msg.send(fail_silently=True)


def send_order_cancelled_customer(order):
    items_data = []
    for item in order.items.select_related('product', 'product__category', 'variant').all():
        image_url = get_product_image(item.product)
        variant_info = ''
        if item.variant:
            variant_info = f"{item.variant.size}{' / ' + item.variant.color if item.variant.color else ''}"
        items_data.append({
            'name': item.name,
            'quantity': item.quantity,
            'price': item.subtotal,
            'image_url': image_url,
            'variant': variant_info,
        })

    if order.user:
        customer_name = order.user.full_name
        customer_email = order.user.email
    else:
        customer_name = order.guest_name
        customer_email = order.guest_email

    items_html = ''
    for item in items_data:
        image_tag = f'<img src="{item["image_url"]}" width="80" height="80" style="object-fit:cover;border-radius:4px;" />' if item['image_url'] else '📦'
        variant_tag = f'<br><small style="color:#888;">Variant: {item["variant"]}</small>' if item['variant'] else ''
        items_html += f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #eee;width:100px;text-align:center;">{image_tag}</td>
            <td style="padding:10px;border-bottom:1px solid #eee;">
                <strong>{item['name']}</strong>
                {variant_tag}
                <br><small>Qty: {item['quantity']}</small>
            </td>
            <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;font-weight:bold;">Rs. {item['price']}</td>
        </tr>
        """

    plain_message = f"""
Hi {customer_name},
Your order {order.order_number} has been cancelled.
Total: Rs. {order.total}
Questions? WhatsApp: +92 333 2742727
— Brand Bazar by Mirsa Team
    """.strip()

    html_message = f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <div style="background:#0a0a0a;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
            <h1 style="color:#b8960c;margin:0;font-size:24px;">BRAND BAZAR</h1>
            <p style="color:#fff;margin:5px 0;font-size:12px;letter-spacing:3px;">BY MIRSA</p>
        </div>
        <div style="background:#fff;padding:20px;border:1px solid #eee;">
            <h2 style="color:#111;">❌ Order Cancelled</h2>
            <p style="color:#555;">Hi <strong>{customer_name}</strong>, we're informing you that your order has been cancelled.</p>

            <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
                <tr><td style="padding:5px;color:#888;">Order</td><td style="padding:5px;font-weight:bold;">{order.order_number}</td></tr>
                <tr><td style="padding:5px;color:#888;">Total</td><td style="padding:5px;">Rs. {order.total}</td></tr>
                <tr><td style="padding:5px;color:#888;">Payment</td><td style="padding:5px;">{order.payment_method.upper()}</td></tr>
            </table>

            <h3 style="color:#111;border-bottom:2px solid #b8960c;padding-bottom:8px;">Cancelled Items</h3>
            <table style="width:100%;border-collapse:collapse;">
                {items_html}
            </table>

            <div style="margin-top:20px;padding:15px;background:#fff3f3;border-radius:8px;text-align:center;border:1px solid #f5c6cb;">
                <p style="margin:0;color:#721c24;font-size:14px;">If you did not request this cancellation, please contact us immediately.</p>
            </div>

            <div style="margin-top:20px;padding:15px;background:#f9f9f9;border-radius:8px;text-align:center;">
                <p style="margin:0;color:#555;font-size:14px;">Contact us on WhatsApp</p>
                <a href="https://wa.me/923332742727" style="color:#25d366;font-weight:bold;font-size:16px;">+92 333 2742727</a>
            </div>
        </div>
        <div style="background:#f5f5f5;padding:10px;text-align:center;font-size:12px;color:#888;border-radius:0 0 8px 8px;">
            Brand Bazar by Mirsa © 2026 | <a href="https://brandbazarbymirsa.com" style="color:#b8960c;">brandbazarbymirsa.com</a>
        </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(
        subject=f'Order {order.order_number} Cancelled — Brand Bazar by Mirsa',
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[customer_email],
    )
    msg.attach_alternative(html_message, "text/html")
    msg.send(fail_silently=True)