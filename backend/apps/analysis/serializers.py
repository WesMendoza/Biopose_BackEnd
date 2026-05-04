"""
SERIALIZERS - Fase 3: Endpoints REST Básicos
============================================

Este módulo define los serializers de Django REST Framework para:
- Procesamiento de imágenes (YOLO)
- Procesamiento de videos (LSTM)
- Generación de frames

Referencias:
- FASE_3_ESPECIFICACION.md - Especificación de endpoints y respuestas
- FASE_3_QUICK_START.md - Guía de implementación
"""

from rest_framework import serializers
from .models import VideoUpload, DetectionEvent, PersonKeypoints, AnalysisReport


# ============================================================================
# SERIALIZERS - KEYPOINTS Y PUNTOS CLAVE
# ============================================================================

class KeypointSerializer(serializers.Serializer):
    """
    Serializa un punto clave (keypoint COCO).
    
    Estructura COCO 17-points:
    - 5 puntos: cara (0: nariz, 1-2: ojos, 3-4: orejas)
    - 6 puntos: brazos (5-6: hombros, 7-8: codos, 9-10: muñecas)
    - 6 puntos: piernas (11-12: caderas, 13-14: rodillas, 15-16: tobillos)
    """
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=50)
    x = serializers.FloatField()
    y = serializers.FloatField()
    z = serializers.FloatField(default=0)
    confidence = serializers.FloatField()


# ============================================================================
# SERIALIZERS - PROCESAMIENTO DE IMÁGENES
# ============================================================================

class ImageUploadSerializer(serializers.Serializer):
    """Recibir imagen para procesar con YOLO."""
    image = serializers.ImageField()
    width = serializers.IntegerField(required=False, allow_null=True)
    height = serializers.IntegerField(required=False, allow_null=True)


class ImageDimensionsSerializer(serializers.Serializer):
    """Dimensiones de una imagen."""
    original_width = serializers.IntegerField()
    original_height = serializers.IntegerField()
    processed_width = serializers.IntegerField()
    processed_height = serializers.IntegerField()


class ImageProcessingResponseSerializer(serializers.Serializer):
    """Respuesta de procesamiento de imagen con YOLO."""
    id = serializers.IntegerField()
    message = serializers.CharField()
    filename = serializers.CharField()
    path = serializers.CharField()
    image_position = serializers.CharField()  # "horizontal", "vertical", "cuadrada"
    keypoints = KeypointSerializer(many=True)
    image_dimensions = ImageDimensionsSerializer()
    processing_time_ms = serializers.IntegerField()
    model = serializers.CharField()


class ImageResizeSerializer(serializers.Serializer):
    """Solicitar redimensionamiento de imagen."""
    image = serializers.ImageField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class ImageSaveSerializer(serializers.Serializer):
    """Guardar imagen + keypoints en BD."""
    image_id = serializers.IntegerField()
    keypoints = KeypointSerializer(many=True)
    image_metadata = serializers.DictField()


# ============================================================================
# SERIALIZERS - PROCESAMIENTO DE VIDEOS
# ============================================================================

class VideoUploadSerializer(serializers.ModelSerializer):
    """Serializar VideoUpload de BD."""
    class Meta:
        model = VideoUpload
        fields = ['id', 'nombre_original', 'ruta_archivo', 'tamaño_bytes',
                  'duracion_segundos', 'estado', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


class VideoUploadFormSerializer(serializers.Serializer):
    """Recibir video para subir."""
    video = serializers.FileField()
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)


class VideoProcessingRequestSerializer(serializers.Serializer):
    """Solicitar procesamiento de video con LSTM."""
    mode = serializers.ChoiceField(
        choices=['operativo', 'analitico', 'debug'],
        help_text="operativo: sin esqueleto | analitico: con esqueleto | debug: debug completo"
    )
    dimension = serializers.ChoiceField(
        choices=['2D', '3D'],
        help_text="2D: detección 2D | 3D: detección 3D"
    )
    fps_skip = serializers.IntegerField(required=False, default=1)
    confidence_threshold = serializers.FloatField(required=False, default=0.75)


class VideoProcessingResponseSerializer(serializers.Serializer):
    """Respuesta al iniciar procesamiento (HTTP 202)."""
    id = serializers.IntegerField()
    status = serializers.CharField()
    task_id = serializers.CharField()
    message = serializers.CharField()
    started_at = serializers.DateTimeField()


# ============================================================================
# SERIALIZERS - EVENTOS Y DETECCIONES
# ============================================================================

class BoundingBoxSerializer(serializers.Serializer):
    """Bounding box de una persona detectada."""
    x1 = serializers.IntegerField()
    y1 = serializers.IntegerField()
    x2 = serializers.IntegerField()
    y2 = serializers.IntegerField()
    person_id = serializers.IntegerField()


class DetectionSummarySerializer(serializers.Serializer):
    """Resumen de una detección en un frame."""
    frame_index = serializers.IntegerField()
    timestamp_sec = serializers.FloatField()
    detections = serializers.ListField()
    bounding_boxes = BoundingBoxSerializer(many=True)


class DetectionEventSerializer(serializers.ModelSerializer):
    """Serializar evento detectado."""
    class Meta:
        model = DetectionEvent
        fields = ['id', 'video', 'tipo_evento', 'confianza', 'frame_inicio',
                  'frame_fin', 'segundo_inicio', 'segundo_fin', 'detalles_json',
                  'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


class PersonKeypointsSerializer(serializers.ModelSerializer):
    """Serializar keypoints de persona detectada."""
    class Meta:
        model = PersonKeypoints
        fields = ['id', 'detection_event', 'person_id', 'frame_index',
                  'keypoints_json', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


# ============================================================================
# SERIALIZERS - REPORTES Y RESULTADOS
# ============================================================================

class AnalysisReportSerializer(serializers.ModelSerializer):
    """Serializar reporte de análisis completo."""
    detections = DetectionEventSerializer(source='detectionevent_set', many=True, read_only=True)
    
    class Meta:
        model = AnalysisReport
        fields = ['id', 'video', 'total_detections', 'detections_by_type',
                  'processing_time_seconds', 'resumen_json', 'detections',
                  'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


class VideoResultsSerializer(serializers.Serializer):
    """Resultados consolidados de un video."""
    id = serializers.IntegerField()
    filename = serializers.CharField()
    status = serializers.CharField()
    processing_mode = serializers.CharField()
    total_frames = serializers.IntegerField()
    duration_seconds = serializers.FloatField()
    processing_time_seconds = serializers.FloatField()
    detections = DetectionEventSerializer(many=True)
    analysis_report = AnalysisReportSerializer()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


# ============================================================================
# SERIALIZERS - SERVER-SENT EVENTS (SSE)
# ============================================================================

class SSEProgressEventSerializer(serializers.Serializer):
    """Evento SSE de progreso."""
    video_id = serializers.IntegerField()
    progress_percent = serializers.IntegerField()
    current_frame = serializers.IntegerField()
    total_frames = serializers.IntegerField()
    processing_time_elapsed_sec = serializers.IntegerField()
    eta_seconds = serializers.IntegerField()
    timestamp = serializers.DateTimeField()


class SSEDetectionEventSerializer(serializers.Serializer):
    """Evento SSE de detección."""
    frame_index = serializers.IntegerField()
    timestamp_sec = serializers.FloatField()
    detections = serializers.ListField()
    bounding_boxes = BoundingBoxSerializer(many=True)
    frame_base64 = serializers.CharField()


class SSECompletedEventSerializer(serializers.Serializer):
    """Evento SSE de finalización."""
    video_id = serializers.IntegerField()
    status = serializers.CharField()
    total_detections = serializers.IntegerField()
    total_processing_time_sec = serializers.FloatField()
    detections_summary = serializers.DictField()


# ============================================================================
# SERIALIZERS - GENERACIÓN DE FRAMES
# ============================================================================

class GenerateFramesRequestSerializer(serializers.Serializer):
    """Solicitar generación de frames desde video."""
    video = serializers.FileField()
    fps_value = serializers.IntegerField(min_value=1, max_value=30)
    max_duration_seconds = serializers.IntegerField(required=False, default=30)


class FrameDataSerializer(serializers.Serializer):
    """Datos de un frame generado."""
    frame_index = serializers.IntegerField()
    timestamp_sec = serializers.FloatField()
    filename = serializers.CharField()
    base64 = serializers.CharField()
    size_bytes = serializers.IntegerField()


class GenerateFramesResponseSerializer(serializers.Serializer):
    """Respuesta de generación de frames."""
    video_filename = serializers.CharField()
    fps_extracted = serializers.IntegerField()
    total_frames_generated = serializers.IntegerField()
    duration_seconds = serializers.FloatField()
    frames = FrameDataSerializer(many=True)
    processing_time_ms = serializers.IntegerField()
    message = serializers.CharField()


# ============================================================================
# SERIALIZERS - ERRORES
# ============================================================================

class ErrorResponseSerializer(serializers.Serializer):
    """Respuesta de error estándar."""
    error = serializers.CharField()
    message = serializers.CharField()


class ValidationErrorSerializer(serializers.Serializer):
    """Respuesta de error de validación (400)."""
    error = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)


class NotFoundErrorSerializer(serializers.Serializer):
    """Respuesta de recurso no encontrado (404)."""
    error = serializers.CharField()
    message = serializers.CharField()


class ServerErrorSerializer(serializers.Serializer):
    """Respuesta de error del servidor (500)."""
    error = serializers.CharField()
    message = serializers.CharField()
