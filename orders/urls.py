from django.urls import path
from . import views

urlpatterns = [
    path('',                     views.OrderListCreateView.as_view(),  name='orders'),
    path('<int:pk>/',            views.OrderDetailView.as_view(),      name='order_detail'),
    path('<int:pk>/cancel/',     views.OrderCancelView.as_view(),      name='order_cancel'),
    path('<int:pk>/status/',     views.OrderStatusUpdateView.as_view(),name='order_status'),
]