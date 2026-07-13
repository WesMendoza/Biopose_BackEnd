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
    POST /api/analysis/media/images/upload/
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
        
        # Obtener idUsuario y idEmpresa desde el token/usuario autenticado
        user = request.user
        id_usuario = None
        id_empresa = None
        if user and user.is_authenticated:
            id_usuario = user
            from apps.gestionEmpresas.models import EmpresaUsuarioRol
            asignacion = EmpresaUsuarioRol.objects.filter(idUsuario=user, estado='A').first()
            if asignacion:
                id_empresa = asignacion.idEmpresa_id

        from apps.analysis.models import ImageUpload
        image_upload = ImageUpload.objects.create(
            idUsuario=id_usuario,
            idEmpresa=id_empresa,
            nombreOriginal=image_file.name,
            rutaArchivoOriginal=f"images/uploads/{filename}",
            tamanioBytes=image_file.size,
            estado="PENDING"
        )
        
        response_data = ImageUploadSerializer(image_upload).data
        return Response(response_data, status=status.HTTP_201_CREATED)


class VideoUploadView(APIView):
    """
    POST /api/analysis/media/videos/upload/
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
        
        # Obtener idUsuario y idEmpresa desde el token/usuario autenticado
        user = request.user
        id_usuario = None
        id_empresa = None
        if user and user.is_authenticated:
            id_usuario = user
            from apps.gestionEmpresas.models import EmpresaUsuarioRol
            asignacion = EmpresaUsuarioRol.objects.filter(idUsuario=user, estado='A').first()
            if asignacion:
                id_empresa = asignacion.idEmpresa_id

        # Guardado en base de datos.
        video_upload = VideoUpload.objects.create(
            idUsuario=id_usuario,
            idEmpresa=id_empresa,
            nombreOriginal=video_file.name,
            rutaArchivo=f"videos/uploads/{filename}",
            tamanioBytes=video_file.size,
            estado="PENDING"
        )
        
        # Disparar limpieza pasiva
        try:
            from apps.analysis.tasks import cleanup_orphaned_media_task
            cleanup_orphaned_media_task.delay()
        except: pass
        
        response_data = VideoUploadSerializer(video_upload).data
        return Response(response_data, status=status.HTTP_201_CREATED)
    
class VideoCleanupView(APIView):
    """
    API para destruir el Video, el JSON y limpiar la Base de Datos.
    Se ejecuta cuando el Frontend abandona la pantalla o pide procesar uno nuevo.
    """
    def delete(self, request, video_id):
        try:
            video = VideoUpload.objects.get(idVideoUpload=video_id)
            
            # 1. Borrar Video Físico (.mp4)
            if video.rutaArchivo:
                video_path = os.path.join(settings.MEDIA_ROOT, str(video.rutaArchivo))
                if os.path.exists(video_path):
                    os.remove(video_path)
            
            # 2. Borrar Reporte Físico (.json) de forma agresiva
            json_filename = f'keypoints_video_{video_id}.json'
            json_path = os.path.join(settings.MEDIA_ROOT, 'reports', json_filename)
            if os.path.exists(json_path):
                os.remove(json_path)
            
            # 3. Borrar de la Base de Datos
            video.delete()
            
            return Response({"message": "Archivos y datos destruidos correctamente"}, status=200)
        except VideoUpload.DoesNotExist:
            # Si el video ya no está en la BD, intentamos borrar el JSON de todos modos
            json_filename = f'keypoints_video_{video_id}.json'
            json_path = os.path.join(settings.MEDIA_ROOT, 'reports', json_filename)
            if os.path.exists(json_path):
                os.remove(json_path)
            return Response({"message": "Limpieza física forzada ejecutada"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)