from django.urls import path
from .views import VideoProcessView, VideoResultsView

urlpatterns = [
    path('videos/<int:video_id>/process/', VideoProcessView.as_view(), name='video-process'),
    path('videos/<int:video_id>/results/', VideoResultsView.as_view(), name='video-results'),
]
