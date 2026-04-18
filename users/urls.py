from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/',           views.RegisterView.as_view(),          name='register'),
    path('login/',              views.LoginView.as_view(),             name='login'),
    path('logout/',             views.LogoutView.as_view(),            name='logout'),
    path('token/refresh/',      TokenRefreshView.as_view(),            name='token_refresh'),
    path('profile/',            views.ProfileView.as_view(),           name='profile'),
    path('addresses/',          views.AddressListCreateView.as_view(), name='addresses'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(),     name='address_detail'),
]