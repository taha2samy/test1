from django.urls import re_path
from . import consumers  # تأكد من أن هذا يشير إلى المستهلكين الصحيحين

websocket_urlpatterns = [
    re_path(r'ws/orders/$', consumers.OrderConsumer.as_asgi()),
]
