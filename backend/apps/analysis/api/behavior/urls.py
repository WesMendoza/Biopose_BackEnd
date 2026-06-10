from django.urls import path
from .views import ProcessVideoView, VideoResultsView, VideoKeypointsJsonView

urlpatterns = [
    path('<int:video_id>/process/', ProcessVideoView.as_view(), name='video-process'),
    path('<int:video_id>/results/', VideoResultsView.as_view(), name='video-results'),
    path('<int:video_id>/keypoints-json/', VideoKeypointsJsonView.as_view(), name='video-keypoints-json'),
]
