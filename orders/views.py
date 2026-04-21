from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer


def get_optimized_order_queryset(user):
    qs = (
        Order.objects
        .select_related('user', 'shipping_address')
        .prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related('product', 'variant')
            )
        )
    )
    if user.is_authenticated and hasattr(user, 'role') and user.role == 'admin':
        return qs.all()
    if user.is_authenticated:
        return qs.filter(user=user)
    return qs.none()


class OrderListCreateView(generics.ListCreateAPIView):
    # Allow anyone to POST (guest checkout), only authenticated can GET
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return get_optimized_order_queryset(self.request.user)
        return Order.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class   = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return get_optimized_order_queryset(self.request.user)


class OrderStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            order = Order.objects.select_related('user').prefetch_related('items').get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=404)

        new_status = request.data.get('status')
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({'error': 'Invalid status.'}, status=400)

        old_status = order.status
        order.status = new_status
        order.save(update_fields=['status'])

        from .emails import send_order_shipped_customer, send_order_cancelled_customer
        if new_status == 'shipped' and old_status != 'shipped':
            send_order_shipped_customer(order)
        elif new_status == 'cancelled' and old_status != 'cancelled':
            send_order_cancelled_customer(order)

        return Response({'message': f'Order status updated to {new_status}.'})


class OrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=404)

        if order.status not in ['pending', 'confirmed']:
            return Response({'error': 'Only pending or confirmed orders can be cancelled.'}, status=400)

        order.status = 'cancelled'
        order.save(update_fields=['status'])

        from .emails import send_order_cancelled_customer
        order_with_user = Order.objects.select_related('user').prefetch_related('items').get(pk=pk)
        send_order_cancelled_customer(order_with_user)

        return Response({'message': 'Order cancelled successfully.'})