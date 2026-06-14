from django.urls import path
from .views import GetLocalFileDataView, ListLocalFilesView, PoseDetectionImageView, SavePoseToDiskView

urlpatterns = [
    # API: /api/analysis/pose/image/ (Carga y procesamiento directo)
    path('image/', PoseDetectionImageView.as_view(), name='pose-detect-image'),
    
    # API: /api/analysis/pose/image/<int:image_id>/process/ (Procesar imagen existente en BD)
    path('image/<int:image_id>/process/', PoseDetectionImageView.as_view(), name='pose-detect-image-process'),
    
    # API: /api/analysis/pose/image/<int:image_id>/save-to-disk/
    path('image/<int:image_id>/save-to-disk/', SavePoseToDiskView.as_view(), name='pose-save-disk'), # <--- SIN LA BARRA AL INICIO

    path('local-files/', ListLocalFilesView.as_view(), name='pose-local-files'),
    path('local-file-data/', GetLocalFileDataView.as_view(), name='pose-local-file-data'),
]