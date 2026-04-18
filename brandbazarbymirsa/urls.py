from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',          admin.site.urls),
    path('api/auth/',       include('users.urls')),
    path('api/products/',   include('products.urls')),
    path('api/orders/',     include('orders.urls')),
    path('api/payments/',   include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin panel branding
admin.site.site_header = 'Brand Bazar'
admin.site.site_title  = 'Brand Bazar Admin'
admin.site.index_title = 'Dashboard'