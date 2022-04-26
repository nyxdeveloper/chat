# chat/routing.py
from django.urls import re_path

from .consumers import ChatConsumer
from .consumers import MessageConsumer

websocket_urlpatterns = [
    # chats
    re_path(r'ws/chats/(?P<pk>\w+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/new_messages/', MessageConsumer.as_asgi())
]
