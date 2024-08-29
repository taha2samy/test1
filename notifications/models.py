from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Driver(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
from django.db import models

class Meal(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Order(models.Model):
    code = models.SlugField(max_length=5, unique=True, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    offer_code = models.TextField(default='', blank=True)  
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey('Meal', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    driver = models.ForeignKey('Driver', related_name='assigned_orders', on_delete=models.SET_NULL, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order {self.code}'
    
@receiver(post_save, sender=Order)
def order_created(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        order_data = {
            'pk': instance.pk,
            'code': instance.code,
            'address': instance.address,
            'city': instance.city,
            'offer_code': instance.offer_code,
            'description': instance.description,
            'status': instance.status,
            'total_price': str(instance.total_price),
            'quantity': instance.quantity,
            'note': instance.note,
            'created_at': instance.created_at.isoformat(),
            'meal': {
                'pk': instance.meal.pk,
                'name': instance.meal.name
            }
        }
        async_to_sync(channel_layer.group_send)(
            'orders',
            {
                'type': 'order_created',
                'order': order_data,
            }
        )
