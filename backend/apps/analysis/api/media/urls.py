from django.urls import path
from .views import ImageUploadView, VideoUploadView, VideoCleanupView

urlpatterns = [
    # API: /api/analysis/media/images/upload/
    path('images/upload/', ImageUploadView.as_view(), name='media-images-upload'),
    
    # API: /api/analysis/media/videos/upload/
    path('videos/upload/', VideoUploadView.as_view(), name='media-videos-upload'),

    # API: /api/analysis/media/videos/<id>/ (ELIMINAR)
    path('videos/<int:video_id>/', VideoCleanupView.as_view(), name='media-videos-cleanup'),
]
