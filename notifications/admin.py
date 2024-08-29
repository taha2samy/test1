from django.contrib import admin
from .models import Order,Meal,Driver

admin.site.register(Order)
# Register your models here.
admin.site.register(Meal)
admin.site.register(Driver)