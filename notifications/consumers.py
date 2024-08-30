import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Order
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import sync_to_async
from .models import Order

class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("WebSocket connection established")
        await self.channel_layer.group_add("orders", self.channel_name)

        # Send all pending orders to the new connection
        pending_orders = await sync_to_async(self.get_pending_orders)()
        pending_orders_data = [
            await sync_to_async(self.serialize_order)(order)
            for order in pending_orders
        ]
        await self.send(text_data=json.dumps({
            'type': 'initial_orders',
            'orders': pending_orders_data
        }))

    async def disconnect(self, close_code):
        print(f"WebSocket connection closed: {close_code}")
        await self.channel_layer.group_discard("orders", self.channel_name)

    async def receive(self, text_data):
        print(f"Data received: {text_data}")
        data = json.loads(text_data)
        order_pk = data.get('orderId')
        if data['type'] == 'accept_order' and order_pk:
            await self.accept_order(order_pk)

    async def accept_order(self, order_pk):
        try:
            order = await sync_to_async(Order.objects.get)(pk=order_pk)
            order.status = 'accepted'
            await sync_to_async(order.save)()
            print(f"Order {order_pk} accepted")

            # Notify all clients that the order has been accepted
            order_data = await sync_to_async(self.serialize_order)(order)
            await self.channel_layer.group_send(
                'orders',
                {
                    'type': 'order_accepted',
                    'order': order_data
                }
            )
        except Order.DoesNotExist:
            print(f"Order {order_pk} does not exist")

    async def order_accepted(self, event):
        print(f"Sending order accepted event: {event['order']['pk']}")
        await self.send(text_data=json.dumps({
            'type': 'order_accepted',
            'order': event['order'],
        }))

    async def order_created(self, event):
        print(f"Sending order created event: {event['order']['pk']}")
        await self.send(text_data=json.dumps({
            'type': 'order_created',
            'order': event['order'],
        }))
    async def order_deleted(self, event):
        print("ordre deleted")
        print(f"Sending order created event: {event['order']['pk']}")
        event['order']['remove']=True
        await self.send(text_data=json.dumps({
            'type': 'order_deleted',
            'order': event['order'],
        }))
    async def order_active(self, event):
        print("ordre active")
        print(f"Sending order created event: {event['order']['pk']}")
        event['order']['active']=True
        await self.send(text_data=json.dumps({
            'type': 'order_active',
            'order': event['order'],
        }))

    def get_pending_orders(self):
        return list(Order.objects.filter(status='pending'))

    def serialize_order(self, order):
        return {
            'pk': order.pk,
            'code': order.code,
            'address': order.address,
            'city': order.city,
            'offer_code': order.offer_code,
            'description': order.description,
            'status': order.status,
            'total_price': str(order.total_price),
            'quantity': order.quantity,
            'note': order.note,
            'created_at': order.created_at.isoformat(),
            'meal': {
                'pk': order.meal.pk,
                'name': order.meal.name
            }
        }
