import os
import cv2
import numpy as np
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import PoseDetectionResponseSerializer
from apps.analysis.api.media.serializers import ImageUploadSerializer

# Importar el servicio IA sanitizado de la Fase 1
from services.pose_detection import PoseDetectionService

class PoseDetectionImageView(APIView):
    """
    POST /api/analysis/pose/image/
    Sube una imagen, la procesa al instante pasándola por YOLO y devuelve los 17 keypoints.
    No interactúa con Django ORM ni guarda metadatos por defecto.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # 1. Validar la imagen de entrada usando nuestro serializador nativo de media/
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": "Invalid upload parameters",
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        image_file = request.FILES['image']
        
        # 2. Leer imagen a RAM (cv2) sin guardar forzosamente al disco
        try:
            image_bytes = np.frombuffer(image_file.read(), np.uint8)
            cv_image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
            if cv_image is None:
                raise ValueError("No se pudo decodificar la imagen.")
        except Exception as e:
            return Response({
                "error": "Corrupted image",
                "message": f"Error procesando los bytes de la imagen: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 3. Mandar a inferencia vía capa de servicios IA (Fase 1)
        try:
            pose_service = PoseDetectionService()
            results_ia, annotated_frame = pose_service.detect_and_draw_pose_frame(cv_image)
            
            # Guardar la imagen procesada
            import uuid
            processed_dir = os.path.join(settings.MEDIA_ROOT, 'images', 'processed')
            os.makedirs(processed_dir, exist_ok=True)
            safe_filename = f"pose_{uuid.uuid4().hex[:8]}.jpg"
            processed_path = os.path.join(processed_dir, safe_filename)
            cv2.imwrite(processed_path, annotated_frame)
            relative_path = f"images/processed/{safe_filename}"
            
        except Exception as e:
            return Response({
                "error": "AI Processing Error",
                "message": f"Falló la inferencia de YOLO: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 4. Validar formato de salida IA e inyectarlos para respuesta
        persons_formatted = []
        for p in results_ia.get('keypoints', []):
            person_coords = p.get('keypoints', [])
            formatted_kps = [
                {"id": i, "name": f"kp_{i}", "x": kp[0], "y": kp[1], "confidence": 1.0}
                for i, kp in enumerate(person_coords)
            ]
            
            persons_formatted.append({
                "person_id": p.get('person_id', 0),
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

        out_serializer = PoseDetectionResponseSerializer(data=response_data)
        out_serializer.is_valid(raise_exception=True)
        
        return Response(out_serializer.validated_data, status=status.HTTP_200_OK)
