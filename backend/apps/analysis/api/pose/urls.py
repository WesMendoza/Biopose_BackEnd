from django.urls import path
from .views import PoseDetectionImageView

urlpatterns = [
    # API: /api/analysis/pose/image/ (Carga y procesamiento directo)
    path('image/', PoseDetectionImageView.as_view(), name='pose-detect-image'),
    
    # API: /api/analysis/pose/image/<int:image_id>/process/ (Procesar imagen existente en BD)
    path('image/<int:image_id>/process/', PoseDetectionImageView.as_view(), name='pose-detect-image-process'),
]
