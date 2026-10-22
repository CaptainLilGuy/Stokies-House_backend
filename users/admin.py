from django.contrib import admin
from .models import DeviceToken, User, AbstractUser


admin.site.register(DeviceToken)
admin.site.register(User)
# Register your models here.
