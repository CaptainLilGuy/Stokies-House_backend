from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/households/', include('households.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/expenses/', include('expenses.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)