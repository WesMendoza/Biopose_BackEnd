import json
import os
import shutil
import cv2
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
    Genera los fotogramas 'al vuelo' desde el video original basado en el JSON 
    y los guarda en la ruta del usuario.
    """
    def post(self, request, video_id):
        video_upload = get_object_or_404(VideoUpload, idVideoUpload=video_id)
        target_path = request.data.get('target_path')
        
        # Obtenemos las dimensiones elegidas en el frontend (ej. 300x445)
        target_width = request.data.get('width', None)
        target_height = request.data.get('height', None)

        if not target_path:
            return Response({"error": "Falta la ruta de guardado (target_path)."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_path = os.path.normpath(target_path)
            dir_imagen = os.path.join(target_path, "Imagen")
            os.makedirs(dir_imagen, exist_ok=True)
            
            # Nombre incremental (ej: 00001, 00002)
            existing_jsons = [f for f in os.listdir(target_path) if f.endswith('.json')]
            next_number = len(existing_jsons) + 1
            video_base_name = f"{next_number:05d}"
            
            # 1. Obtener Reporte y ruta del JSON
            try:
                reporte = AnalysisReport.objects.get(idVideoUpload=video_upload)
                source_json_path = _resolve_media_path(reporte.rutaJsonKeypoints)
                if not source_json_path or not os.path.exists(source_json_path):
                    return Response({"error": "El JSON de resultados no existe en el servidor."}, status=status.HTTP_404_NOT_FOUND)
            except AnalysisReport.DoesNotExist:
                return Response({"error": "No hay un reporte de análisis generado para este video."}, status=status.HTTP_404_NOT_FOUND)

            # 2. Copiar el JSON a la carpeta seleccionada
            dest_json_path = os.path.join(target_path, f"{video_base_name}.json")
            shutil.copy2(source_json_path, dest_json_path)

            # 3. EXTRAER FOTOGRAMAS DEL VIDEO ORIGINAL AL VUELO
            video_file_path = _resolve_media_path(video_upload.rutaArchivo)
            if not video_file_path or not os.path.exists(video_file_path):
                return Response({"error": "El video original no se encuentra."}, status=status.HTTP_404_NOT_FOUND)

            # Leer el JSON para saber qué segundos extraer
            with open(source_json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Detectar en qué nodo guardas los frames (depende de la salida de Celery)
            frames_list = []
            if isinstance(json_data, dict):
                frames_list = json_data.get('keypoints_data') or json_data.get('keypoints') or json_data.get('frames') or json_data.get('data') or []
            elif isinstance(json_data, list):
                frames_list = json_data

            # Abrir el video
            cap = cv2.VideoCapture(video_file_path)
            
            for idx, frame_info in enumerate(frames_list):
                # Extraemos el tiempo exacto en que ocurrió la detección
                timestamp_sec = frame_info.get('timestamp_sec', frame_info.get('time', 0))
                
                # Movemos el cursor del video a ese milisegundo exacto
                cap.set(cv2.CAP_PROP_POS_MSEC, float(timestamp_sec) * 1000)
                success, frame = cap.read()
                
                if success:
                    # Aplicar redimensionamiento si el usuario lo seleccionó
                    #if target_width and target_height:
                        #try:
                            #frame = cv2.resize(frame, (int(target_width), int(target_height)))
                       # except Exception:
                            #pass # Si falla por alguna razón, guarda el original
                            
                    # Guardar como 00001_frame_001.jpg
                    dest_name = f"{video_base_name}_frame_{idx+1:03d}.jpg"
                    dest_path = os.path.join(dir_imagen, dest_name)
                    cv2.imwrite(dest_path, frame)
                    
            cap.release()

            return Response({
                "success": True, 
                "message": f"Colección exportada exitosamente como {video_base_name}"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)