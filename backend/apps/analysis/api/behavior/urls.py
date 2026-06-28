from django.urls import path
from .views import ProcessVideoView, SaveVideoToDiskView, VideoResultsView, VideoKeypointsJsonView

urlpatterns = [
    path('<int:video_id>/process/', ProcessVideoView.as_view(), name='video-process'),
    path('<int:video_id>/results/', VideoResultsView.as_view(), name='video-results'),
    path('<int:video_id>/keypoints-json/', VideoKeypointsJsonView.as_view(), name='video-keypoints-json'),
    path('<int:video_id>/save-to-disk/', SaveVideoToDiskView.as_view(), name='video-save-disk'),
]
