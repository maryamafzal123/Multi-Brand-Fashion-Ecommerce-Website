from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.conf import settings
from orders.models import Order
from .models import Payment
from .utils import (
    jazzcash_build_payload,
    jazzcash_verify_callback,
    easypaisa_build_payload,
    easypaisa_verify_callback,
)


class InitiatePaymentView(APIView):
    """
    POST /api/payments/initiate/
    Body: { "order_id": 5, "method": "jazzcash" }
    Returns gateway URL + payload to POST from frontend.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        method   = request.data.get('method')

        if not order_id or not method:
            return Response(
                {'error': 'order_id and method are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch order with select_related — single query
        try:
            order = (
                Order.objects
                .select_related('user')
                .get(id=order_id, user=request.user)
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if order.payment_status == 'paid':
            return Response(
                {'error': 'Order is already paid.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create payment record
        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={'method': method, 'amount': order.total}
        )

        if method == 'jazzcash':
            payload = jazzcash_build_payload(order)
            return Response({
                'gateway_url': settings.JAZZCASH_POST_URL,
                'payload':     payload,
            })

        elif method == 'easypaisa':
            payload = easypaisa_build_payload(order)
            return Response({
                'gateway_url': settings.EASYPAISA_POST_URL,
                'payload':     payload,
            })

        elif method == 'cod':
            with transaction.atomic():
                payment.status = 'pending'
                payment.save(update_fields=['status'])
                order.status   = 'confirmed'
                order.save(update_fields=['status'])
            return Response({
                'message':  'COD order confirmed successfully.',
                'order_id': order.id,
            })

        return Response(
            {'error': 'Invalid payment method.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class JazzCashCallbackView(APIView):
    """
    JazzCash POSTs back to this endpoint after payment.
    Verifies hash then updates payment and order status.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data          = dict(request.data)
        response_code = data.get('pp_ResponseCode')
        txn_ref       = data.get('pp_TxnRefNo', '')

        # Verify hash — reject if tampered
        if not jazzcash_verify_callback(data):
            return Response(
                {'error': 'Invalid hash. Request rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract order ID from TxnRefNo (format: T<order_id><timestamp>)
        try:
            order_id = int(''.join(filter(str.isdigit, txn_ref))[:len(str(txn_ref))])
            # More reliable extraction
            digits   = ''.join(filter(str.isdigit, txn_ref[1:]))
            order_id = int(digits[:len(digits)//2]) if digits else None
            order    = Order.objects.select_related().get(id=order_id)
            payment  = order.payment
        except Exception:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if response_code == '000':
            payment.mark_success(
                transaction_id=txn_ref,
                gateway_response=data
            )
        else:
            payment.mark_failed(gateway_response=data)

        return Response({'message': 'Callback processed successfully.'})


class EasyPaisaCallbackView(APIView):
    """
    EasyPaisa POSTs back to this endpoint after payment.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data          = dict(request.data)
        order_ref     = data.get('orderRefNum', '')
        response_code = data.get('responseCode')

        # Verify hash
        if not easypaisa_verify_callback(data):
            return Response(
                {'error': 'Invalid hash. Request rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # orderRefNum format: EP<order_id>
            order_id = int(order_ref.replace('EP', ''))
            order    = Order.objects.get(id=order_id)
            payment  = order.payment
        except Exception:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if response_code == '0000':
            payment.mark_success(
                transaction_id=data.get('transactionId', ''),
                gateway_response=data
            )
        else:
            payment.mark_failed(gateway_response=data)

        return Response({'message': 'Callback processed successfully.'})