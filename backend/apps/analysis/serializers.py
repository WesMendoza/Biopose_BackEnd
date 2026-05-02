from rest_framework import serializers
from .models import VideoUpload, DetectionEvent, AnalysisReport, SystemParameter

class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoUpload
        fields = '__all__'
        read_only_fields = ('idVideoUpload', 'fechaCarga', 'fechaProcesamiento')

class DetectionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionEvent
        fields = '__all__'
        read_only_fields = ('idDetectionEvent', 'fechaCreacion')

class AnalysisReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisReport
        fields = '__all__'
        read_only_fields = ('idAnalysisReport', 'generadoEn')

class SystemParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemParameter
        fields = '__all__'
