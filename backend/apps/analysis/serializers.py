"""
SERIALIZERS - Fase 3: Endpoints REST Básicos
============================================

Serializers para imágenes, videos, detecciones, reportes y eventos SSE.
"""

from rest_framework import serializers

from .models import AnalysisReport, DetectionEvent, PersonKeypoints, VideoUpload


class KeypointSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=50)
    x = serializers.FloatField()
    y = serializers.FloatField()
    z = serializers.FloatField(default=0)
    confidence = serializers.FloatField()


class ImageDimensionsSerializer(serializers.Serializer):
    original_width = serializers.IntegerField()
    original_height = serializers.IntegerField()
    processed_width = serializers.IntegerField()
    processed_height = serializers.IntegerField()


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    width = serializers.IntegerField(required=False, allow_null=True)
    height = serializers.IntegerField(required=False, allow_null=True)


class ImageProcessingResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    message = serializers.CharField()
    filename = serializers.CharField()
    path = serializers.CharField()
    image_position = serializers.CharField()
    keypoints = KeypointSerializer(many=True)
    image_dimensions = ImageDimensionsSerializer()
    processing_time_ms = serializers.IntegerField()
    model = serializers.CharField()


class ImageResizeSerializer(serializers.Serializer):
    image = serializers.ImageField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class ImageSaveSerializer(serializers.Serializer):
    image_id = serializers.IntegerField()
    keypoints = KeypointSerializer(many=True)
    image_metadata = serializers.DictField()


class VideoUploadFormSerializer(serializers.Serializer):
    video = serializers.FileField()
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)


class VideoUploadSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='idVideoUpload', read_only=True)
    id_usuario = serializers.IntegerField(source='idUsuario_id', read_only=True, allow_null=True)
    id_empresa = serializers.IntegerField(source='idEmpresa', read_only=True, allow_null=True)
    nombre_original = serializers.CharField(source='nombreOriginal')
    ruta_archivo = serializers.CharField(source='rutaArchivo')
    tamanio_bytes = serializers.IntegerField(source='tamanioBytes')
    duracion_segundos = serializers.FloatField(source='duracionSegundos', allow_null=True)
    fps = serializers.FloatField(allow_null=True)
    estado = serializers.CharField()
    celery_task_id = serializers.CharField(source='celeryTaskId', allow_null=True)
    fecha_carga = serializers.DateTimeField(source='fechaCarga', read_only=True)
    fecha_procesamiento = serializers.DateTimeField(source='fechaProcesamiento', allow_null=True, required=False)


class VideoProcessingRequestSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=['operativo', 'analitico', 'debug'])
    dimension = serializers.ChoiceField(choices=['2D', '3D'])
    fps_skip = serializers.IntegerField(required=False, default=1, min_value=1)
    confidence_threshold = serializers.FloatField(required=False, default=0.75, min_value=0.0, max_value=1.0)


class VideoProcessingResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    task_id = serializers.CharField()
    message = serializers.CharField()
    started_at = serializers.DateTimeField()


class BoundingBoxSerializer(serializers.Serializer):
    x1 = serializers.IntegerField()
    y1 = serializers.IntegerField()
    x2 = serializers.IntegerField()
    y2 = serializers.IntegerField()
    person_id = serializers.IntegerField()


class DetectionEventSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='idDetectionEvent', read_only=True)
    video = serializers.IntegerField(source='idVideoUpload_id')
    tipo_evento = serializers.CharField(source='tipoEvento')
    confianza = serializers.FloatField()
    frame_inicio = serializers.IntegerField(source='frameInicio')
    frame_fin = serializers.IntegerField(source='frameFin')
    segundo_inicio = serializers.FloatField(source='tiempoInicio')
    segundo_fin = serializers.FloatField(source='tiempoFin')
    detalles_json = serializers.JSONField(source='detalles', allow_null=True, required=False)
    fecha_creacion = serializers.DateTimeField(source='fechaCreacion', read_only=True)


class PersonKeypointsSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='idPersonKeypoints', read_only=True)
    detection_event = serializers.IntegerField(source='idDetectionEvent_id')
    person_id = serializers.IntegerField(source='personId')
    frame_index = serializers.IntegerField(source='frameNumber')
    keypoints_json = serializers.JSONField(source='keypointsJson')
    fecha_creacion = serializers.DateTimeField(source='fechaCreacion', read_only=True)


class AnalysisReportSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='idAnalysisReport', read_only=True)
    video = serializers.IntegerField(source='idVideoUpload_id')
    total_detections = serializers.IntegerField(source='totalEventos')
    detections_by_type = serializers.DictField(source='estadisticas', allow_null=True, required=False)
    processing_time_seconds = serializers.FloatField(source='tiempoProcesamientoSegundos', allow_null=True)
    resumen_json = serializers.JSONField(source='resumenJson', allow_null=True, required=False)
    detections = serializers.SerializerMethodField()
    fecha_creacion = serializers.DateTimeField(source='fechaCreacion', read_only=True)
    fecha_actualizacion = serializers.DateTimeField(source='actualizadoEn', read_only=True)

    def get_detections(self, obj):
        video = getattr(obj, 'idVideoUpload', None)
        if video is None:
            return []
        return DetectionEventSerializer(video.eventos.all(), many=True).data


class VideoResultsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    filename = serializers.CharField()
    status = serializers.CharField()
    processing_mode = serializers.CharField()
    total_frames = serializers.IntegerField()
    duration_seconds = serializers.FloatField()
    processing_time_seconds = serializers.FloatField()
    detections = DetectionEventSerializer(many=True)
    analysis_report = AnalysisReportSerializer(allow_null=True, required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True, required=False)


class SSEProgressEventSerializer(serializers.Serializer):
    video_id = serializers.IntegerField()
    progress_percent = serializers.IntegerField()
    current_frame = serializers.IntegerField()
    total_frames = serializers.IntegerField()
    processing_time_elapsed_sec = serializers.FloatField()
    eta_seconds = serializers.FloatField()
    timestamp = serializers.DateTimeField()


class SSEDetectionEventSerializer(serializers.Serializer):
    frame_index = serializers.IntegerField()
    timestamp_sec = serializers.FloatField()
    detections = serializers.ListField()
    bounding_boxes = BoundingBoxSerializer(many=True)
    frame_base64 = serializers.CharField()


class SSECompletedEventSerializer(serializers.Serializer):
    video_id = serializers.IntegerField()
    status = serializers.CharField()
    total_detections = serializers.IntegerField()
    total_processing_time_sec = serializers.FloatField()
    detections_summary = serializers.DictField()


class GenerateFramesRequestSerializer(serializers.Serializer):
    video = serializers.FileField()
    fps_value = serializers.IntegerField(min_value=1, max_value=30)
    max_duration_seconds = serializers.IntegerField(required=False, default=30, min_value=1)


class FrameDataSerializer(serializers.Serializer):
    frame_index = serializers.IntegerField()
    timestamp_sec = serializers.FloatField()
    filename = serializers.CharField()
    base64 = serializers.CharField()
    size_bytes = serializers.IntegerField()


class GenerateFramesResponseSerializer(serializers.Serializer):
    video_filename = serializers.CharField()
    fps_extracted = serializers.IntegerField()
    total_frames_generated = serializers.IntegerField()
    duration_seconds = serializers.FloatField()
    frames = FrameDataSerializer(many=True)
    processing_time_ms = serializers.IntegerField()
    message = serializers.CharField()
