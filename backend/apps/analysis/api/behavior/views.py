from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from apps.analysis.models import VideoUpload, AnalysisReport
from apps.analysis.tasks import process_video_task

class ProcessVideoView(APIView):
    """
    Endpoint para enviar un video a procesar asíncronamente vía Celery (Fase 4).
    """
    def post(self, request, video_id):
        # Verificar que el video existe
        video_upload = get_object_or_404(VideoUpload, idVideoUpload=video_id)
        
        # Validar estado
        if video_upload.estado in ['PROCESSING', 'COMPLETED']:
            return Response({
                "message": f"El video ya está {video_upload.estado}."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Parámetros de optimización (por defecto los de Fase 3/4)
        mode = request.data.get('mode', 'operativo')
        dimension = request.data.get('dimension', '2D')
        fps_skip = int(request.data.get('fps_skip', 5))
        confidence_threshold = float(request.data.get('confidence_threshold', 0.75))

        # Enviar la tarea a Celery de forma asíncrona (.delay)
        task = process_video_task.delay(
            video_id=video_upload.idVideoUpload,
            mode=mode,
            dimension=dimension,
            fps_skip=fps_skip,
            confidence_threshold=confidence_threshold
        )

        return Response({
            "id": video_upload.idVideoUpload,
            "status": "processing",
            "task_id": task.id,
            "message": "Video en procesamiento asíncrono. Puedes consultar progreso luego."
        }, status=status.HTTP_202_ACCEPTED)


class VideoResultsView(APIView):
    """
    Endpoint para obtener los resultados finales de un video procesado.
    """
    def get(self, request, video_id):
        video_upload = get_object_or_404(VideoUpload, idVideoUpload=video_id)
        
        if video_upload.estado == 'PROCESSING':
            return Response({
                "id": video_upload.idVideoUpload,
                "status": "processing",
                "message": "El procesamiento aún está en curso."
            }, status=status.HTTP_202_ACCEPTED)
            
        if video_upload.estado == 'FAILED':
            return Response({
                "id": video_upload.idVideoUpload,
                "status": "failed",
                "message": "Hubo un error crítico al procesar el video."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            reporte = AnalysisReport.objects.get(idVideoUpload=video_upload)
            # En un entorno real se serializaría con AnalysisReportSerializer
            return Response({
                "id": video_upload.idVideoUpload,
                "status": "completed",
                "total_frames": reporte.totalFrames,
                "duration_seconds": reporte.totalDuracionSegundos,
                "processing_time_seconds": reporte.tiempoProcesamientoSegundos,
                "analysis_report": {
                    "total_detections": reporte.totalEventos,
                    "detections_by_type": reporte.estadisticas.get('detections_by_type', {}),
                    "average_confidence": reporte.confianzaPromedio,
                }
            }, status=status.HTTP_200_OK)
        except AnalysisReport.DoesNotExist:
            return Response({
                "message": "Reporte no encontrado, pero el video está como COMPLETED. Estado inconsistente."
            }, status=status.HTTP_404_NOT_FOUND)
