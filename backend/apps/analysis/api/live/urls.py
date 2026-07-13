from django.urls import path
from . import views

urlpatterns = [
    path('stream/', views.live_stream_sse, name='live-stream-sse'),
    path('stream-multiperson/', views.live_action_multiperson_stream_sse, name='live-action-multiperson-stream-sse'),
    path('detections/', views.live_detections, name='live-detections'),
]
