from django.contrib import admin
from .models import Household, HouseholdMember
# Register your models here.
admin.site.register(Household)
admin.site.register(HouseholdMember)