import os
import cv2
import json
import base64
import uuid
import shutil
import zipfile
import io
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import PoseDetectionResponseSerializer
from services.pose_detection import PoseDetectionService
from apps.analysis.models import ImageUpload

class PoseDetectionImageView(APIView):
    """
    POST /api/analysis/pose/image/<image_id>/process/
    Procesa la imagen usando YOLO y guarda los resultados INTERNOS en MEDIA_ROOT para la UI.
    """
    def post(self, request, image_id, *args, **kwargs):
        try:
            image_record = ImageUpload.objects.get(pk=image_id)
        except ImageUpload.DoesNotExist:
            return Response({
                "error": "Image not found",
                "message": f"La imagen con ID {image_id} no existe."
            }, status=status.HTTP_404_NOT_FOUND)

        if image_record.estado == "PROCESSING":
            return Response({"error": "Already processing"}, status=status.HTTP_400_BAD_REQUEST)

        image_record.estado = "PROCESSING"
        image_record.save()

        # Leer imagen del servidor
        image_path = os.path.join(settings.MEDIA_ROOT, image_record.rutaArchivoOriginal)
        if not os.path.exists(image_path):
            image_record.estado = "FAILED"
            image_record.save()
            return Response({"error": "File missing"}, status=status.HTTP_404_NOT_FOUND)

        cv_image = cv2.imread(image_path)
        if cv_image is None:
            image_record.estado = "FAILED"
            image_record.save()
            return Response({"error": "Corrupted image"}, status=status.HTTP_400_BAD_REQUEST)

        # Inferencia con YOLO
        try:
            pose_service = PoseDetectionService()
            results_ia, annotated_frame = pose_service.detect_and_draw_pose_frame(cv_image)
            
            # Guardado interno del Back
            processed_dir = os.path.join(settings.MEDIA_ROOT, 'images', 'processed')
            os.makedirs(processed_dir, exist_ok=True)
            safe_filename = f"pose_{uuid.uuid4().hex[:8]}.jpg"
            relative_path = f"images/processed/{safe_filename}"
            
            cv2.imwrite(os.path.join(processed_dir, safe_filename), annotated_frame)
            
            image_record.rutaArchivoProcesado = relative_path
            image_record.estado = "COMPLETED"
            image_record.fechaProcesamiento = timezone.now()
            image_record.save()
            
        except Exception as e:
            image_record.estado = "FAILED"
            image_record.save()
            return Response({"error": "AI Processing Error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Formatear Keypoints
        persons_formatted = []
        all_persons_data = results_ia.get('keypoints', [])
        all_confidences = results_ia.get('confidences', [])

        for idx, p in enumerate(all_persons_data):
            person_coords = p.get('keypoints', [])
            person_confs = all_confidences[idx] if idx < len(all_confidences) else []
            
            formatted_kps = []
            for i, kp in enumerate(person_coords):
                conf = float(person_confs[i]) if i < len(person_confs) else 0.0
                formatted_kps.append({
                    "id": i, 
                    "name": f"kp_{i}", 
                    "x": float(kp[0]), 
                    "y": float(kp[1]), 
                    "confidence": conf
                })
            
            persons_formatted.append({
                "person_id": p.get('person_id', idx),
                "bbox": {"x1": 0, "y1": 0, "x2": 0, "y2": 0}, 
                "keypoints": formatted_kps
            })

        response_data = {
            "success": True,
            "model_used": "yolov8s-pose",
            "position": "unknown", 
            "persons_detected": len(persons_formatted),
            "processed_image_path": relative_path,
            "persons": persons_formatted
        }

        # Guardar copia intermedia del JSON en los reportes internos del back
        try:
            reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            json_filename = f"keypoints_image_{image_record.pk}.json"
            
            with open(os.path.join(reports_dir, json_filename), 'w', encoding='utf-8') as json_file:
                json.dump(response_data, json_file, ensure_ascii=False, indent=4)
                
            image_record.rutaArchivoJson = f"reports/{json_filename}"
            image_record.save()
        except Exception as e:
            print(f"Advertencia: No se pudo guardar el reporte JSON interno: {str(e)}")

        out_serializer = PoseDetectionResponseSerializer(data=response_data)
        out_serializer.is_valid(raise_exception=True)
        return Response(out_serializer.validated_data, status=status.HTTP_200_OK)


class SavePoseToDiskView(APIView):
    """
    POST /api/analysis/pose/image/<image_id>/save-to-disk/
    Genera el ZIP de una SOLA IMAGEN y luego elimina los archivos temporales.
    """
    def post(self, request, image_id, *args, **kwargs):
        try:
            image_record = ImageUpload.objects.get(pk=image_id)
        except ImageUpload.DoesNotExist:
            return Response({"error": "Registro no encontrado en BD"}, status=status.HTTP_404_NOT_FOUND)

        results_payload = request.data.get('results')

        if not results_payload:
            return Response({"error": "Faltan los resultados JSON ('results')"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            zip_buffer = io.BytesIO()
            source_image_path = os.path.join(settings.MEDIA_ROOT, str(image_record.rutaArchivoOriginal))
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                json_string = json.dumps(results_payload, ensure_ascii=False, indent=4)
                zip_file.writestr("0001.json", json_string)
                
                if os.path.exists(source_image_path):
                    zip_file.write(source_image_path, arcname="Imagen/0001.jpg")
                else:
                    return Response({"error": "La imagen física no se encuentra en el servidor."}, status=status.HTTP_404_NOT_FOUND)
            
            # ELIMINACIÓN DE ARCHIVOS FÍSICOS
            if image_record.rutaArchivoOriginal and os.path.exists(source_image_path):
                os.remove(source_image_path)
            
            if image_record.rutaArchivoProcesado:
                proc_path = os.path.join(settings.MEDIA_ROOT, str(image_record.rutaArchivoProcesado))
                if os.path.exists(proc_path):
                    os.remove(proc_path)
                    
            if image_record.rutaArchivoJson:
                json_path = os.path.join(settings.MEDIA_ROOT, str(image_record.rutaArchivoJson))
                if os.path.exists(json_path):
                    os.remove(json_path)

            image_record.delete() 

            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="Dataset_Imagen_{image_id}.zip"'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            
            return response

        except Exception as e:
            return Response({
                "error": "Error al generar ZIP",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==========================================
# NUEVA VISTA PARA EL BATCH (CARRITO)
# ==========================================
class SaveBatchImagesToDiskView(APIView):
    """
    POST /api/analysis/pose/batch/save-to-disk/
    Recibe un LOTE (array) de imágenes procesadas y genera un solo archivo ZIP ordenado.
    """
    def post(self, request):
        batch_data = request.data.get('batch', [])
        
        if not batch_data or not isinstance(batch_data, list):
            return Response({"error": "Se requiere un arreglo 'batch' con los datos de las imágenes."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for idx, item in enumerate(batch_data):
                    image_id = item.get('imageId')
                    results_payload = item.get('results')
                    
                    if not image_id or not results_payload:
                        continue
                        
                    file_prefix = f"{(idx + 1):04d}"
                    
                    try:
                        image_upload = ImageUpload.objects.get(pk=image_id)
                        source_image_path = os.path.join(settings.MEDIA_ROOT, str(image_upload.rutaArchivoOriginal))
                        
                        if os.path.exists(source_image_path):
                            # 1. Escribir imagen en el ZIP
                            zip_file.write(source_image_path, arcname=f"Imagen/{file_prefix}.jpg")
                            
                            # 2. Escribir JSON en el ZIP
                            json_string = json.dumps(results_payload, ensure_ascii=False, indent=4)
                            zip_file.writestr(f"{file_prefix}.json", json_string)
                            
                            # 3. Limpiar servidor
                            os.remove(source_image_path)
                            
                            if image_upload.rutaArchivoProcesado:
                                proc_path = os.path.join(settings.MEDIA_ROOT, str(image_upload.rutaArchivoProcesado))
                                if os.path.exists(proc_path): os.remove(proc_path)
                                
                            if image_upload.rutaArchivoJson:
                                json_path = os.path.join(settings.MEDIA_ROOT, str(image_upload.rutaArchivoJson))
                                if os.path.exists(json_path): os.remove(json_path)

                            image_upload.delete()
                            
                    except ImageUpload.DoesNotExist:
                        pass 

            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="Dataset_Lote_{len(batch_data)}_Imagenes.zip"'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            
            return response
            
        except Exception as e:
            return Response({"error": "Error al generar el ZIP por lotes", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListLocalFilesView(APIView):
    # ... (Manten tu código original)
    def post(self, request, *args, **kwargs):
        target_path = request.data.get('target_path')
        if not target_path:
            return Response({"error": "Ruta no proporcionada"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_path = os.path.normpath(target_path)
            dir_imagen = os.path.join(target_path, "Imagen")
            
            if not os.path.exists(dir_imagen):
                return Response([]) # Carpeta vacía o no existe
                
            files = sorted([f for f in os.listdir(dir_imagen) if f.endswith(('.jpg', '.jpeg', '.png'))])
            # Devolvemos un formato amigable para el frontend
            file_list = [{"id": f, "name": f} for f in files]
            return Response(file_list, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetLocalFileDataView(APIView):
    # ... (Manten tu código original)
    def post(self, request, *args, **kwargs):
        target_path = request.data.get('target_path')
        file_name = request.data.get('file_name') # Ej: 00001.jpg o 00001_frame_001.jpg
        
        if not target_path or not file_name:
            return Response({"error": "Faltan parámetros"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            target_path = os.path.normpath(target_path)
            img_path = os.path.join(target_path, "Imagen", file_name)
            
            if not os.path.exists(img_path):
                return Response({"error": "La imagen física no se encontró"}, status=status.HTTP_404_NOT_FOUND)
                
            # 1. Convertir imagen a Base64
            with open(img_path, "rb") as img_file:
                b64_string = base64.b64encode(img_file.read()).decode('utf-8')
                
            base_name = os.path.splitext(file_name)[0] # '00001' o '00001_frame_001'
            json_data = None
            
            # =============================================================
            # LÓGICA INTELIGENTE DE LECTURA DE JSON
            # =============================================================
            if "_frame_" in base_name:
                # CASO A: Es un fotograma de video (Ej: 00001_frame_001)
                video_base, frame_str = base_name.split("_frame_")
                json_path = os.path.join(target_path, f"{video_base}.json")
                frame_idx = int(frame_str) - 1 # _frame_001 -> index 0 del array
                
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as jf:
                        full_json = json.load(jf)
                        
                    # Si el JSON maestro vino como string, lo parseamos
                    if isinstance(full_json, str):
                        full_json = json.loads(full_json)
                        
                    # Buscar la lista de frames dentro del JSON del video
                    frames_list = []
                    if isinstance(full_json, dict):
                        frames_list = full_json.get('keypoints_data') or full_json.get('keypoints') or full_json.get('frames') or full_json.get('data') or []
                    elif isinstance(full_json, list):
                        frames_list = full_json
                        
                    # Si la lista de frames vino como string, la parseamos
                    if isinstance(frames_list, str):
                        frames_list = json.loads(frames_list)
                        
                    # Extraer el fotograma específico
                    if 0 <= frame_idx < len(frames_list):
                        frame_info = frames_list[frame_idx]
                        
                        # Si el frame individual es string, lo parseamos
                        if isinstance(frame_info, str):
                            frame_info = json.loads(frame_info)
                            
                        raw_pts = []
                        if isinstance(frame_info, dict):
                            raw_pts = frame_info.get('keypoints_json') or frame_info.get('keypoints') or []
                        elif isinstance(frame_info, list):
                            raw_pts = frame_info
                            
                        # ¡AQUÍ ESTÁ LA MAGIA! Si raw_pts es texto, lo convertimos a lista
                        if isinstance(raw_pts, str):
                            try:
                                raw_pts = json.loads(raw_pts)
                            except Exception:
                                raw_pts = []
                        
                        persons_list = []
                        if raw_pts and isinstance(raw_pts, list):
                            # Verificar si es un arreglo de arreglos (Multipersona)
                            if len(raw_pts) > 0 and isinstance(raw_pts[0], list):
                                for p_idx, pts in enumerate(raw_pts):
                                    persons_list.append({"person_id": p_idx, "keypoints": pts})
                            else:
                                # Una sola persona
                                persons_list.append({"person_id": 0, "keypoints": raw_pts})
                                
                        # Evitamos usar .get() si full_json es una lista
                        modelo_usado = "YOLOv8-pose (Video)"
                        if isinstance(full_json, dict):
                            modelo_usado = full_json.get("model_used", "YOLOv8-pose (Video)")
                                
                        # Construir el objeto falso idéntico al de imágenes estáticas
                        json_data = {
                            "model_used": modelo_usado,
                            "persons_detected": len(persons_list),
                            "persons": persons_list
                        }
            else:
                # CASO B: Es una imagen estática normal (Ej: 00001.json)
                json_path = os.path.join(target_path, f"{base_name}.json")
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as jf:
                        json_data = json.load(jf)
            # =============================================================
                        
            return Response({
                "image_b64": f"data:image/jpeg;base64,{b64_string}",
                "json_data": json_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)