from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import VideoUpload, DetectionEvent, AnalysisReport, SystemParameter
from .serializers import (
    VideoUploadSerializer, 
    DetectionEventSerializer, 
    AnalysisReportSerializer,
    SystemParameterSerializer
)

class VideoUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de videos subidos.
    Permite listar, crear, obtener detalles y eliminar videos.
    """
    queryset = VideoUpload.objects.all()
    serializer_class = VideoUploadSerializer
    
    @action(detail=True, methods=['get'])
    def eventos(self, request, pk=None):
        """Retorna todos los eventos de detección para un video específico."""
        video = self.get_object()
        eventos = video.eventos.all()
        serializer = DetectionEventSerializer(eventos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reporte(self, request, pk=None):
        """Retorna el reporte consolidado de un video."""
        video = self.get_object()
        try:
            reporte = video.reporte
            serializer = AnalysisReportSerializer(reporte)
            return Response(serializer.data)
        except:
            return Response({'error': 'No hay reporte para este video'}, 
                          status=status.HTTP_404_NOT_FOUND)


class DetectionEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet para eventos de detección.
    Permite listar y obtener detalles de eventos.
    """
    queryset = DetectionEvent.objects.all()
    serializer_class = DetectionEventSerializer
    
    def get_queryset(self):
        """Filtra eventos por video si se proporciona el parámetro video_id."""
        queryset = super().get_queryset()
        video_id = self.request.query_params.get('video_id')
        if video_id:
            queryset = queryset.filter(video_id=video_id)
        return queryset


class AnalysisReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para reportes de análisis (solo lectura).
    """
    queryset = AnalysisReport.objects.all()
    serializer_class = AnalysisReportSerializer


class SystemParameterViewSet(viewsets.ModelViewSet):
    """
    ViewSet para parámetros del sistema.
    Permite consultar y modificar configuración.
    """
    queryset = SystemParameter.objects.all()
    serializer_class = SystemParameterSerializer
    lookup_field = 'codigo'

