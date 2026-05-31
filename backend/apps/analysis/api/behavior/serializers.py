from rest_framework import serializers
from apps.analysis.models import DetectionEvent, AnalysisReport

class DetectionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionEvent
        fields = ['id', 'video', 'tipo_evento', 'confianza', 'frame_inicio',
                  'frame_fin', 'segundo_inicio', 'segundo_fin', 'detalles_json', 'fecha_creacion']

class AnalysisReportSerializer(serializers.ModelSerializer):
    detections = DetectionEventSerializer(source='detectionevent_set', many=True, read_only=True)
    
    class Meta:
        model = AnalysisReport
        fields = ['id', 'video', 'total_detections', 'detections_by_type',
                  'processing_time_seconds', 'resumen_json', 'detections', 'fecha_creacion', 'fecha_actualizacion']

class VideoProcessRequestSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["operativo", "analitico", "debug"], default="operativo")
    dimension = serializers.ChoiceField(choices=["2D", "3D"], default="2D")
    fps_skip = serializers.IntegerField(default=5, min_value=1)
    confidence_threshold = serializers.FloatField(default=0.75, min_value=0.0, max_value=1.0)
