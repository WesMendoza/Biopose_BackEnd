# FASE 3: GUÍA PRÁCTICA DE INICIO RÁPIDO

**Objetivo**: Servir como referencia histórica y técnica de la Fase 3 ya implementada en el backend Django.

**Importante**: La Fase 3 ya quedó implementada a nivel base en `backend/`; este documento conserva el contexto técnico y los ejemplos de uso para prueba y mantenimiento.

---

## PASO 1: VALIDAR ENTORNO

Antes de comenzar, verifica que tienes todo listo:

```bash
# 1. Entorno virtual activo
cd backend
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# 2. Dependencias de Django instaladas
pip list | findstr "django djangorestframework"

# 3. BD funcionando
python manage.py check
# Esperado: "System check identified no issues (0 silenced)."

# 4. Servicios IA disponibles
python test_services.py
# Esperado: "✅ TODOS LOS SERVICIOS DE IA FUNCIONAN CORRECTAMENTE"
```

Si alguno falla, regresa a **Fase 1 y 2**.

---

## PASO 2: ESTRUCTURA BASE DE ARCHIVOS

Los siguientes archivos YA EXISTEN (de ejercicios anteriores):
- ✅ `backend/apps/analysis/models.py` (Fase 2)
- ✅ `backend/apps/analysis/migrations/` (Fase 2)
- ✅ `backend/services/` (Fase 1)

Ahora vamos a crear los archivos para Fase 3:

```
backend/apps/analysis/
├── models.py                    # YA EXISTE
├── admin.py
├── apps.py
├── tests.py
├── views.py                     # 🆕 CREAR
├── serializers.py               # 🆕 CREAR
├── urls.py                      # 🆕 ACTUALIZAR
├── permissions.py               # 🆕 CREAR (opcional)
├── pagination.py                # 🆕 CREAR (opcional)
└── migrations/
```

---

## PASO 3: CREAR `serializers.py`

**Archivo**: `backend/apps/analysis/serializers.py`

```python
from rest_framework import serializers
from .models import VideoUpload, DetectionEvent, PersonKeypoints, AnalysisReport


class KeypointSerializer(serializers.Serializer):
    """Serializar un punto clave (keypoint COCO)"""
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=50)
    x = serializers.FloatField()
    y = serializers.FloatField()
    z = serializers.FloatField(default=0)
    confidence = serializers.FloatField()


class ImageUploadSerializer(serializers.Serializer):
    """Recibir imagen para procesar con YOLO"""
    image = serializers.ImageField()
    width = serializers.IntegerField(required=False, allow_null=True)
    height = serializers.IntegerField(required=False, allow_null=True)


class ImageProcessingResponseSerializer(serializers.Serializer):
    """Respuesta de procesamiento de imagen"""
    id = serializers.IntegerField()
    message = serializers.CharField()
    filename = serializers.CharField()
    path = serializers.CharField()
    image_position = serializers.CharField()  # "horizontal", "vertical", "cuadrada"
    keypoints = KeypointSerializer(many=True)
    image_dimensions = serializers.DictField()
    processing_time_ms = serializers.IntegerField()
    model = serializers.CharField()


class VideoUploadSerializer(serializers.ModelSerializer):
    """Serializar VideoUpload de BD"""
    class Meta:
        model = VideoUpload
        fields = ['id', 'nombre_original', 'ruta_archivo', 'tamaño_bytes',
                  'duracion_segundos', 'estado', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


class VideoUploadFormSerializer(serializers.Serializer):
    """Recibir video para subir"""
    video = serializers.FileField()
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)


class VideoProcessingRequestSerializer(serializers.Serializer):
    """Solicitar procesamiento de video"""
    mode = serializers.ChoiceField(choices=['operativo', 'analitico', 'debug'])
    dimension = serializers.ChoiceField(choices=['2D', '3D'])
    fps_skip = serializers.IntegerField(required=False, default=1)
    confidence_threshold = serializers.FloatField(required=False, default=0.75)


class DetectionEventSerializer(serializers.ModelSerializer):
    """Serializar evento detectado"""
    class Meta:
        model = DetectionEvent
        fields = ['id', 'video', 'tipo_evento', 'confianza', 'frame_inicio',
                  'frame_fin', 'segundo_inicio', 'segundo_fin', 'detalles_json',
                  'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


class PersonKeypointsSerializer(serializers.ModelSerializer):
    """Serializar keypoints de persona"""
    class Meta:
        model = PersonKeypoints
        fields = ['id', 'detection_event', 'person_id', 'frame_index',
                  'keypoints_json', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


class AnalysisReportSerializer(serializers.ModelSerializer):
    """Serializar reporte de análisis"""
    detections = DetectionEventSerializer(source='detectionevent_set', many=True, read_only=True)
    
    class Meta:
        model = AnalysisReport
        fields = ['id', 'video', 'total_detections', 'detections_by_type',
                  'processing_time_seconds', 'resumen_json', 'detections',
                  'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


class GenerateFramesRequestSerializer(serializers.Serializer):
    """Solicitar generación de frames desde video"""
    video = serializers.FileField()
    fps_value = serializers.IntegerField(min_value=1, max_value=30)
    max_duration_seconds = serializers.IntegerField(required=False, default=30)


class FrameResponseSerializer(serializers.Serializer):
    """Respuesta de un frame generado"""
    frame_index = serializers.IntegerField()
    timestamp_sec = serializers.FloatField()
    filename = serializers.CharField()
    base64 = serializers.CharField()
    size_bytes = serializers.IntegerField()


class GenerateFramesResponseSerializer(serializers.Serializer):
    """Respuesta de generación de frames"""
    video_filename = serializers.CharField()
    fps_extracted = serializers.IntegerField()
    total_frames_generated = serializers.IntegerField()
    duration_seconds = serializers.FloatField()
    frames = FrameResponseSerializer(many=True)
    processing_time_ms = serializers.IntegerField()
    message = serializers.CharField()
```

---

## PASO 4: CREAR `views.py`

**Archivo**: `backend/apps/analysis/views.py`

```python
import os
import json
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.conf import settings

from .models import VideoUpload, DetectionEvent, AnalysisReport
from .serializers import (
    ImageUploadSerializer, ImageProcessingResponseSerializer,
    VideoUploadSerializer, VideoUploadFormSerializer,
    VideoProcessingRequestSerializer, AnalysisReportSerializer,
    GenerateFramesRequestSerializer, GenerateFramesResponseSerializer,
    DetectionEventSerializer
)

# Importar servicios IA (Fase 1)
from backend.services.pose_detection import detect_pose_yolo
from backend.services.behavior_detection import detect_behavior_lstm
from backend.services.video_processor import process_video_frames


class ImageAnalysisViewSet(viewsets.ViewSet):
    """Endpoints para análisis de imágenes"""
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        POST /api/analysis/images/upload/
        Procesa imagen con YOLO (detección de pose)
        """
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        image_file = serializer.validated_data['image']
        
        try:
            # 1. Guardar imagen temporalmente
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"image_{timestamp}.jpg"
            filepath = default_storage.save(f"images/uploads/{filename}", image_file)
            full_path = os.path.join(settings.MEDIA_ROOT, filepath)

            # 2. Procesar con YOLO
            keypoints, image_position = detect_pose_yolo(full_path)

            # 3. Formatear respuesta
            response_data = {
                'id': 1,  # Placeholder hasta integrar BD
                'message': 'Imagen procesada exitosamente.',
                'filename': filename,
                'path': filepath,
                'image_position': image_position,
                'keypoints': keypoints,
                'image_dimensions': {
                    'original_width': image_file.image.width if hasattr(image_file, 'image') else 1920,
                    'original_height': image_file.image.height if hasattr(image_file, 'image') else 1080,
                    'processed_width': 640,
                    'processed_height': 480
                },
                'processing_time_ms': 1250,
                'model': 'yolov8s-pose'
            }

            serializer = ImageProcessingResponseSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': 'Processing failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def resize(self, request):
        """
        POST /api/analysis/images/resize/
        Redimensiona imagen a dimensiones especificadas
        """
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        image_file = serializer.validated_data['image']
        width = serializer.validated_data.get('width')
        height = serializer.validated_data.get('height')

        if not width or not height:
            return Response(
                {'error': 'Invalid parameters', 'message': 'width y height son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # TODO: Implementar redimensionamiento con OpenCV/PIL
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"image_resized_{timestamp}.jpg"
            filepath = default_storage.save(f"images/processed/{filename}", image_file)

            return Response({
                'message': 'Imagen redimensionada exitosamente.',
                'filename': filename,
                'path': filepath,
                'new_dimensions': {
                    'width': width,
                    'height': height
                },
                'original_dimensions': {
                    'width': 1920,
                    'height': 1080
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': 'Processing failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def save(self, request):
        """
        POST /api/analysis/images/save/
        Guarda imagen + keypoints en BD
        """
        try:
            data = request.data
            image_id = data.get('image_id')
            keypoints = data.get('keypoints', [])
            
            # TODO: Persistir en BD usando modelos
            # image = Image.objects.get(id=image_id)
            # for kpt in keypoints:
            #     Keypoint.objects.create(image=image, ...)

            return Response({
                'success': True,
                'message': 'Imagen y keypoints guardados exitosamente.',
                'image_id': image_id,
                'created_at': datetime.now().isoformat(),
                'storage_path': 'media/images/processed/image.jpg'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VideoAnalysisViewSet(viewsets.ModelViewSet):
    """Endpoints para análisis de videos"""
    queryset = VideoUpload.objects.all()
    serializer_class = VideoUploadSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request):
        """
        POST /api/analysis/videos/upload/
        Sube un video a la BD
        """
        serializer = VideoUploadFormSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        video_file = serializer.validated_data['video']
        description = serializer.validated_data.get('description', '')

        try:
            # 1. Guardar archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"video_{timestamp}.mp4"
            filepath = default_storage.save(f"videos/uploads/{filename}", video_file)
            
            # 2. Crear registro en BD
            video_upload = VideoUpload.objects.create(
                id_empresa=1,  # TODO: Obtener del usuario autenticado
                nombre_original=video_file.name,
                ruta_archivo=filepath,
                tamaño_bytes=video_file.size,
                duracion_segundos=0,  # TODO: Extraer con ffprobe
                estado='uploaded',
                usuario_creacion=1  # TODO: Obtener del request.user
            )

            serializer = VideoUploadSerializer(video_upload)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': 'Upload failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        POST /api/analysis/videos/{id}/process/
        Inicia procesamiento de video con LSTM
        """
        video = self.get_object()
        
        serializer = VideoProcessingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        mode = serializer.validated_data['mode']
        dimension = serializer.validated_data['dimension']

        try:
            # TODO: Integrar Celery en Fase 4
            # task = process_video_task.delay(video.id, mode, dimension)
            
            # Por ahora, procesamiento sincróno
            detections = detect_behavior_lstm(
                os.path.join(settings.MEDIA_ROOT, video.ruta_archivo),
                mode=mode,
                dimension=dimension
            )

            # Guardar detecciones en BD
            for detection in detections:
                DetectionEvent.objects.create(
                    video=video,
                    tipo_evento=detection['tipo_evento'],
                    confianza=detection['confianza'],
                    frame_inicio=detection.get('frame_inicio', 0),
                    frame_fin=detection.get('frame_fin', 0),
                    segundo_inicio=detection.get('segundo_inicio', 0),
                    segundo_fin=detection.get('segundo_fin', 0),
                    detalles_json=json.dumps(detection)
                )

            video.estado = 'completed'
            video.save()

            return Response({
                'id': video.id,
                'status': 'processing',
                'task_id': 'dummy-task-id',
                'message': 'Video en procesamiento.',
                'started_at': datetime.now().isoformat()
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response(
                {'error': 'Processing failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        """
        GET /api/analysis/videos/{id}/stream/
        Stream SSE con progreso y eventos
        
        NOTA: Implementación simplificada. En producción usar django-sse.
        """
        video = self.get_object()
        
        def event_stream():
            # TODO: Implementar streaming real
            yield f"event: progress\ndata: {json.dumps({'progress_percent': 50})}\n\n"
            yield f"event: completed\ndata: {json.dumps({'status': 'completed'})}\n\n"

        from django.http import StreamingHttpResponse
        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        GET /api/analysis/videos/{id}/results/
        Obtiene resultados consolidados
        """
        video = self.get_object()
        detections = DetectionEvent.objects.filter(video=video)
        report = AnalysisReport.objects.filter(video=video).first()

        response_data = {
            'id': video.id,
            'filename': video.nombre_original,
            'status': video.estado,
            'detections': DetectionEventSerializer(detections, many=True).data,
            'analysis_report': AnalysisReportSerializer(report).data if report else {}
        }

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        GET /api/analysis/videos/{id}/download/
        Descarga video procesado
        """
        video = self.get_object()
        
        from django.http import FileResponse
        filepath = os.path.join(settings.MEDIA_ROOT, video.ruta_archivo)
        
        try:
            return FileResponse(
                open(filepath, 'rb'),
                as_attachment=True,
                filename=f"video_processed_{video.id}.mp4"
            )
        except FileNotFoundError:
            return Response(
                {'error': 'Video not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class FrameGenerationViewSet(viewsets.ViewSet):
    """Endpoints para generación de frames desde videos"""
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['post'])
    def generate_from_video(self, request):
        """
        POST /api/analysis/frames/generate-from-video/
        Extrae frames de un video según FPS especificado
        """
        serializer = GenerateFramesRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        video_file = serializer.validated_data['video']
        fps_value = serializer.validated_data['fps_value']

        try:
            # TODO: Implementar extracción real con OpenCV
            frames = [
                {
                    'frame_index': i,
                    'timestamp_sec': i / fps_value,
                    'filename': f'frame_{i}.jpg',
                    'base64': 'data:image/jpeg;base64,/9j/4AAQ...',
                    'size_bytes': 45234
                }
                for i in range(0, 10)  # Placeholder: 10 frames
            ]

            response_data = {
                'video_filename': video_file.name,
                'fps_extracted': fps_value,
                'total_frames_generated': len(frames),
                'duration_seconds': len(frames) / fps_value,
                'frames': frames,
                'processing_time_ms': 2500,
                'message': f'Frames generados exitosamente. Total: {len(frames)} imágenes.'
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': 'Processing failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

---

## PASO 5: ACTUALIZAR `urls.py`

**Archivo**: `backend/apps/analysis/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImageAnalysisViewSet, VideoAnalysisViewSet, FrameGenerationViewSet

router = DefaultRouter()
router.register(r'videos', VideoAnalysisViewSet, basename='videos')
router.register(r'images', ImageAnalysisViewSet, basename='images')
router.register(r'frames', FrameGenerationViewSet, basename='frames')

urlpatterns = [
    path('', include(router.urls)),
]
```

---

## PASO 6: ACTUALIZAR `core/urls.py`

**Archivo**: `backend/core/urls.py`

Agregar esta línea en `urlpatterns`:

```python
path('api/analysis/', include('apps.analysis.urls')),
```

---

## PASO 7: PROBAR ENDPOINTS

```bash
# 1. Iniciar servidor
python manage.py runserver

# 2. Abrir Postman o cURL

# ENDPOINT 1: Subir Imagen
POST http://localhost:8000/api/analysis/images/upload/
Content-Type: multipart/form-data
image: [seleccionar archivo JPG/PNG]

# ENDPOINT 2: Subir Video
POST http://localhost:8000/api/analysis/videos/upload/
Content-Type: multipart/form-data
video: [seleccionar archivo MP4]

# ENDPOINT 3: Procesar Video
POST http://localhost:8000/api/analysis/videos/1/process/
Content-Type: application/json
{
  "mode": "operativo",
  "dimension": "2D"
}

# ENDPOINT 4: Obtener Resultados
GET http://localhost:8000/api/analysis/videos/1/results/

# ENDPOINT 5: Generar Frames
POST http://localhost:8000/api/analysis/frames/generate-from-video/
Content-Type: multipart/form-data
video: [archivo MP4]
fps_value: 5
```

---

## PASO 8: NEXT STEPS

Una vez que los primeros endpoints funcionen:

1. **Integrar Servicios IA Real**:
   - Reemplazar `detect_pose_yolo()` con implementación real
   - Reemplazar `detect_behavior_lstm()` con implementación real
   - Validar que retornan el formato esperado

2. **Persistencia en BD**:
   - Completar modelo de `Image` (si es necesario)
   - Guardar keypoints en BD para cada imagen
   - Crear índices para búsqueda rápida

3. **Streaming SSE Real**:
   - Implementar progreso real durante procesamiento
   - Emitir eventos de detección en tiempo real
   - Usar Django Channels o django-sse

4. **Pruebas Exhaustivas**:
   - Test con videos de varios tamaños
   - Test con imágenes de resoluciones diferentes
   - Test de errores (archivo corrupto, etc)
   - Load testing con videos largos

5. **Documentación API**:
   - Generar Swagger/OpenAPI
   - Documentar respuestas exactas
   - Documentar códigos de error

---

## DEBUGGING COMMON ISSUES

### Problema 1: "ModuleNotFoundError: No module named 'backend.services'"

**Solución**: Verificar que `backend/services/__init__.py` existe

```bash
touch backend/services/__init__.py
```

### Problema 2: "Imagen no se procesa"

**Solución**: Verificar que los servicios IA funcionan

```bash
python test_services.py
```

### Problema 3: "MEDIA_ROOT no está configurado"

**Solución**: En `settings.py`, agregar:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

Y en `urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [...]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## CHECKLIST FINAL

- [ ] Serializers creados y sin errores
- [ ] Views creados y sin errores
- [ ] URLs configuradas
- [ ] Servidor inicia sin errores
- [ ] Endpoint `/api/analysis/images/upload/` funciona
- [ ] Endpoint `/api/analysis/videos/upload/` funciona
- [ ] Endpoint `/api/analysis/videos/{id}/process/` funciona
- [ ] Endpoint `/api/analysis/videos/{id}/results/` retorna JSON
- [ ] Endpoint `/api/analysis/frames/generate-from-video/` funciona
- [ ] Respuestas JSON tienen estructura consistente
- [ ] Errores manejados correctamente (400, 404, 500)

---

**¡Listo para comenzar Fase 3!** 🚀
