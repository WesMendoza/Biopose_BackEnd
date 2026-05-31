from django.urls import path
from .views import ImageUploadView, VideoUploadView

urlpatterns = [
    # API: /api/analysis/images/upload/
    path('images/upload/', ImageUploadView.as_view(), name='media-images-upload'),
    
    # API: /api/analysis/videos/upload/
    path('videos/upload/', VideoUploadView.as_view(), name='media-videos-upload'),
]
