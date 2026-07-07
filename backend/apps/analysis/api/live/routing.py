from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/live-detection/$', consumers.LiveDetectionConsumer.as_asgi()),
    re_path(r'ws/live-action-multiperson/$', consumers.LiveActionMultiPersonConsumer.as_asgi()),
]
