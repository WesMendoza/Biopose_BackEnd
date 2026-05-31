from django.urls import path
from .views import PoseDetectionImageView

urlpatterns = [
    # API: /api/analysis/pose/image/
    path('image/', PoseDetectionImageView.as_view(), name='pose-detect-image'),
]
