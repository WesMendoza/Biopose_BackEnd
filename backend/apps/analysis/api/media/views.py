import os
from uuid import uuid4
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import ImageUploadSerializer, VideoUploadSerializer
from apps.analysis.models import VideoUpload

class ImageUploadView(APIView):
    """
    POST /api/analysis/images/upload/
    Sube y prepara una imagen para ser posteriormente procesada por YOLO.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": "Invalid parameters",
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # Validar peso (Max 10MB aprox)
        if image_file.size > 10 * 1024 * 1024:
            return Response({
                "error": "File too large",
                "message": "El archivo excede el tamaño máximo permitido (10MB)."
            }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'images', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        ext = os.path.splitext(image_file.name)[1]
        safe_filename = f"img_{uuid4().hex[:8]}{ext}"
        
        fs = FileSystemStorage(location=upload_dir)
        filename = fs.save(safe_filename, image_file)
        
        return Response({
            "message": "Imagen subida lista para procesar",
            "filename": filename,
            "path": f"images/uploads/{filename}"
        }, status=status.HTTP_201_CREATED)


class VideoUploadView(APIView):
    """
    POST /api/analysis/videos/upload/
    Sube un video en bruto y deja su registro inicial en BD (estado PENDING).
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = VideoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": "No video provided",
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        video_file = request.FILES['video']
        
        # Control de tamaño: 50MB
        if video_file.size > 50 * 1024 * 1024:
            return Response({
                "error": "File too large",
                "message": "El archivo excede el tamaño máximo permitido (50MB)."
            }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        ext = os.path.splitext(video_file.name)[1]
        safe_filename = f"vid_{uuid4().hex[:8]}{ext}"
        
        fs = FileSystemStorage(location=upload_dir)
        filename = fs.save(safe_filename, video_file)
        
        # Guardado en base de datos.
        # idUsuario y idEmpresa se inyectarán en la Fase 6 con request.user si es autenticado.
        # Por ahora se permiten NULL según modelo de BD si es legacy.
        video_upload = VideoUpload.objects.create(
            nombreOriginal=video_file.name,
            rutaArchivo=f"videos/uploads/{filename}",
            tamanioBytes=video_file.size,
            estado="PENDING"
        )
        
        response_data = VideoUploadSerializer(video_upload).data
        return Response(response_data, status=status.HTTP_201_CREATED)
