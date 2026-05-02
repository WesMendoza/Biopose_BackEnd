from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VideoUploadViewSet, 
    DetectionEventViewSet, 
    AnalysisReportViewSet,
    SystemParameterViewSet
)

router = DefaultRouter()
router.register(r'videos', VideoUploadViewSet, basename='video')
router.register(r'eventos', DetectionEventViewSet, basename='evento')
router.register(r'reportes', AnalysisReportViewSet, basename='reporte')
router.register(r'parametros', SystemParameterViewSet, basename='parametro')

urlpatterns = [
    path('', include(router.urls)),
]
