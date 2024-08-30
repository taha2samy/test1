from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.signals import post_save,pre_save,post_delete
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
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
    ]
    code = models.SlugField(max_length=5, unique=True, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    offer_code = models.TextField(default='', blank=True)  
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey('Meal', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    driver = models.ForeignKey('Driver', related_name='assigned_orders', on_delete=models.SET_NULL, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order {self.code}'
    
@receiver(post_delete)
def order_delated(sender,instance, **kwargs):
    if instance.status == "pending":
        send_order_to_group(instance,'order_deleted')
@receiver(post_save, sender=Order)
def order_created_or_status_changed(sender, instance, created, **kwargs):
    
    if created:
        if instance.status == "pending":
            send_order_to_group(instance, 'order_created')
    else:
        if instance.status == "active":
            print("1111111111111111")
            send_order_to_group(instance, 'order_active')
        elif instance.status == "pending":
            print("222222222222222")
            send_order_to_group(instance, 'order_created')

def send_order_to_group(instance, typed):
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
        'created_at': instance.created_at.isoformat(),  # Now this will not be None
        'meal': {
            'pk': instance.meal.pk,
            'name': instance.meal.name
        }
    }
    async_to_sync(channel_layer.group_send)(
        'orders',
        {
            'type': typed,
            'order': order_data,
        }
    )
