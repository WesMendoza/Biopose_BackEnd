"""
URL Configuration - Fase 3: Endpoints REST Básicos
==================================================

Rutas para endpoints de análisis:
- /api/analysis/images/ - Procesamiento de imágenes
- /api/analysis/videos/ - Procesamiento de videos
- /api/analysis/frames/ - Generación de frames
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ImageAnalysisViewSet,
    VideoAnalysisViewSet,
    FrameGenerationViewSet,
)

router = DefaultRouter()
router.register(r'images', ImageAnalysisViewSet, basename='image')
router.register(r'videos', VideoAnalysisViewSet, basename='video')
router.register(r'frames', FrameGenerationViewSet, basename='frame')

urlpatterns = [
    path('', include(router.urls)),
]

# Rutas expandidas (alternativo si se prefiere rutas explícitas):
# urlpatterns = [
#     # Imágenes
#     path('images/upload/', ImageAnalysisViewSet.as_view({'post': 'upload'}), name='image-upload'),
#     path('images/resize/', ImageAnalysisViewSet.as_view({'post': 'resize'}), name='image-resize'),
#     path('images/save/', ImageAnalysisViewSet.as_view({'post': 'save'}), name='image-save'),
#     
#     # Videos
#     path('videos/upload/', VideoAnalysisViewSet.as_view({'post': 'upload'}), name='video-upload'),
#     path('videos/<int:pk>/process/', VideoAnalysisViewSet.as_view({'post': 'process'}), name='video-process'),
#     path('videos/<int:pk>/stream/', VideoAnalysisViewSet.as_view({'get': 'stream'}), name='video-stream'),
#     path('videos/<int:pk>/results/', VideoAnalysisViewSet.as_view({'get': 'results'}), name='video-results'),
#     path('videos/<int:pk>/download/', VideoAnalysisViewSet.as_view({'get': 'download'}), name='video-download'),
#     
#     # Frames
#     path('frames/generate-from-video/', FrameGenerationViewSet.as_view({'post': 'generate_from_video'}), name='frame-generate'),
# ]

