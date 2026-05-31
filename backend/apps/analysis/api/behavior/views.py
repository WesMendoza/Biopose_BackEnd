from django.utils import timezone
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.analysis.models import VideoUpload, AnalysisReport
from .serializers import VideoProcessRequestSerializer, AnalysisReportSerializer

class VideoProcessView(APIView):
    """
    POST /api/analysis/videos/{video_id}/process/
    Inicia el procesamiento asíncrono de un video usando el modelo LSTM.
    """
    def post(self, request, video_id, *args, **kwargs):
        try:
            video = VideoUpload.objects.get(pk=video_id)
        except VideoUpload.DoesNotExist:
            return Response({
                "error": "Video not found",
                "message": f"El video con ID {video_id} no existe."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = VideoProcessRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": "Invalid parameters",
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # TODO: En la Fase 4 aquí se llamará a Celery
        # task = process_video_task.delay(video.id, serializer.validated_data)
        
        # Simulación de asignación de tarea para Fase 3 (sin Celery aún)
        dummy_task_id = f"celery-task-uuid-{uuid.uuid4().hex[:8]}"
        video.estado = "PROCESSING"
        video.celery_task_id = dummy_task_id
        video.save()

        return Response({
            "id": video.idVideoUpload if hasattr(video, 'idVideoUpload') else video.pk,
            "status": "processing",
            "task_id": dummy_task_id,
            "message": f"Video en procesamiento. Puedes consultar progreso en /api/analysis/videos/{video_id}/stream/",
            "started_at": timezone.now()
        }, status=status.HTTP_202_ACCEPTED)


class VideoResultsView(APIView):
    """
    GET /api/analysis/videos/{video_id}/results/
    Retorna los resultados consolidados (detecciones) de un video procesado.
    """
    def get(self, request, video_id, *args, **kwargs):
        try:
            video = VideoUpload.objects.get(pk=video_id)
        except VideoUpload.DoesNotExist:
            return Response({
                "error": "Video not found",
                "message": f"El video con ID {video_id} no existe."
            }, status=status.HTTP_404_NOT_FOUND)

        if video.estado == "PROCESSING":
            return Response({
                "id": video.idVideoUpload if hasattr(video, 'idVideoUpload') else video.pk,
                "status": "processing",
                "progress_percent": 0, # Placeholder hasta integrar WebSocket/Celery
                "message": "Procesamiento en curso. Intenta de nuevo más tarde."
            }, status=status.HTTP_202_ACCEPTED)

        # Retornamos el reporte si existe
        try:
            report = AnalysisReport.objects.get(video=video)
            serializer = AnalysisReportSerializer(report)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except AnalysisReport.DoesNotExist:
            return Response({
                "error": "Report not found",
                "message": "El video aún no tiene un reporte de análisis generado."
            }, status=status.HTTP_404_NOT_FOUND)
