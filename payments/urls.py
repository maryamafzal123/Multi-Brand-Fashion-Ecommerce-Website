from django.urls import path
from . import views

urlpatterns = [
    path('initiate/',             views.InitiatePaymentView.as_view(),   name='payment_initiate'),
    path('jazzcash/callback/',    views.JazzCashCallbackView.as_view(),   name='jazzcash_callback'),
    path('easypaisa/callback/',   views.EasyPaisaCallbackView.as_view(), name='easypaisa_callback'),
]