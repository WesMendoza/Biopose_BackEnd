import json
import os
import shutil
import cv2
import zipfile
import io
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from apps.analysis.models import VideoUpload, AnalysisReport
from apps.analysis.tasks import process_video_task


def _resolve_media_path(stored_path):
    if not stored_path:
        return None
    if os.path.isabs(stored_path):
        return stored_path
    return os.path.join(settings.MEDIA_ROOT, stored_path)

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
        analysis_type = request.data.get('analysis_type', 'multipersona')

        # Enviar la tarea a Celery de forma asíncrona (.delay)
        task = process_video_task.delay(
            video_id=video_upload.idVideoUpload,
            mode=mode,
            dimension=dimension,
            fps_skip=fps_skip,
            confidence_threshold=confidence_threshold,
            analysis_type=analysis_type
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
                "ruta_json_keypoints": reporte.rutaJsonKeypoints,
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


class VideoKeypointsJsonView(APIView):
    """
    Endpoint para devolver el contenido del JSON con keypoints generado para un video.
    """
    def get(self, request, video_id):
        video_upload = get_object_or_404(VideoUpload, idVideoUpload=video_id)

        if video_upload.estado == 'PROCESSING':
            return Response({
                "id": video_upload.idVideoUpload,
                "status": "processing",
                "message": "El procesamiento aún está en curso."
            }, status=status.HTTP_202_ACCEPTED)

        try:
            reporte = AnalysisReport.objects.get(idVideoUpload=video_upload)
        except AnalysisReport.DoesNotExist:
            return Response({
                "message": "No existe un reporte asociado para este video."
            }, status=status.HTTP_404_NOT_FOUND)

        json_path = _resolve_media_path(reporte.rutaJsonKeypoints)
        if not json_path or not os.path.exists(json_path):
            return Response({
                "message": "No se encontró el archivo JSON de keypoints.",
                "ruta_json_keypoints": reporte.rutaJsonKeypoints
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            with open(json_path, 'r', encoding='utf-8') as json_file:
                keypoints_payload = json.load(json_file)
        except Exception as exc:
            return Response({
                "message": "No se pudo leer el archivo JSON de keypoints.",
                "error": str(exc),
                "ruta_json_keypoints": reporte.rutaJsonKeypoints
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "id": video_upload.idVideoUpload,
            "status": video_upload.estado.lower(),
            "report_id": reporte.idAnalysisReport,
            "ruta_json_keypoints": reporte.rutaJsonKeypoints,
            "keypoints": keypoints_payload,
        }, status=status.HTTP_200_OK)

class SaveVideoToDiskView(APIView):
    """
    POST /api/analysis/videos/<video_id>/save-to-disk/
    Genera un archivo ZIP en memoria RAM extrayendo los fotogramas del video al vuelo,
    agrega el JSON con los puntos y elimina los archivos del servidor para ahorrar espacio.
    """
    def post(self, request, video_id):
        video_upload = get_object_or_404(VideoUpload, idVideoUpload=video_id)
        
        # Recibimos el JSON modificado por el usuario desde React
        results_payload = request.data.get('results') 
        target_w = request.data.get('width')
        target_h = request.data.get('height')

        if not results_payload:
            return Response({"error": "Faltan los resultados (results)."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Crear un "archivo" en la memoria RAM
            zip_buffer = io.BytesIO()
            video_file_path = _resolve_media_path(video_upload.rutaArchivo)
            
            if not video_file_path or not os.path.exists(video_file_path):
                return Response({"error": "El video original no se encuentra en el servidor."}, status=status.HTTP_404_NOT_FOUND)

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                
                # 2. Escribir el JSON en la raíz del ZIP (ej: 00001.json)
                json_string = json.dumps(results_payload, ensure_ascii=False, indent=4)
                zip_file.writestr("00001.json", json_string)
                
                # 3. Leer el video y extraer fotogramas al vuelo
                cap = cv2.VideoCapture(video_file_path)
                
                # Detectar estructura del JSON
                frames_list = []
                if isinstance(results_payload, dict):
                    frames_list = results_payload.get('keypoints_data') or results_payload.get('keypoints') or results_payload.get('frames') or results_payload.get('data') or []
                elif isinstance(results_payload, list):
                    frames_list = results_payload

                for idx, frame_info in enumerate(frames_list):
                    timestamp_sec = frame_info.get('timestamp_sec', frame_info.get('time', 0))
                    
                    # Nos movemos al segundo exacto del frame
                    cap.set(cv2.CAP_PROP_POS_MSEC, float(timestamp_sec) * 1000)
                    success, frame = cap.read()
                    
                    if success:
                        # Redimensionar el fotograma si el frontend lo solicita (optimiza RAM, peso y velocidad del ZIP)
                        if target_w and target_h:
                            try:
                                frame = cv2.resize(frame, (int(target_w), int(target_h)))
                            except Exception as e:
                                pass # Si falla el redimensionamiento, usamos el original

                        # ¡MAGIA! Convertimos la imagen de OpenCV a bytes en memoria sin tocar el disco
                        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                        if ret:
                            # Escribimos los bytes directamente dentro de la carpeta "Imagen/" del ZIP
                            dest_name = f"Imagen/00001_frame_{idx+1:03d}.jpg"
                            zip_file.writestr(dest_name, buffer.tobytes())
                            
                cap.release()

            # 4. === ELIMINACIÓN DE ARCHIVOS FÍSICOS (Limpieza de AWS) ===
            
            # Borrar video original subido
            if video_upload.rutaArchivo and os.path.exists(video_file_path):
                os.remove(video_file_path)
            
            # Borrar el reporte JSON generado internamente por Celery
            try:
                reporte = AnalysisReport.objects.get(idVideoUpload=video_upload)
                report_path = _resolve_media_path(reporte.rutaJsonKeypoints)
                if report_path and os.path.exists(report_path):
                    os.remove(report_path)
                reporte.delete() # Borramos el registro del reporte
            except AnalysisReport.DoesNotExist:
                pass
            
            # Borrar el registro del video para dejar BD limpia
            video_upload.delete()

            # 5. Enviar el ZIP resultante al usuario
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="Dataset_VideoFrames.zip"'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            
            return response
            
        except Exception as e:
            return Response({"error": "Error al generar el ZIP", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)