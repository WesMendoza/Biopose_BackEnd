from rest_framework import serializers
from apps.analysis.models import VideoUpload

class ImageUploadSerializer(serializers.Serializer):
    """
    Serializer nativo para validar cargas de imágenes aisladas.
    No está anclado a un modelo de BD porque las imágenes se procesan al vuelo.
    """
    image = serializers.ImageField(
        required=True,
        error_messages={
            "required": "No image provided", 
            "invalid": "Debes enviar un archivo de imagen válido."
        }
    )
    # Parametros opcionales para control de dimension (usado por YOLO)
    height = serializers.IntegerField(required=False, min_value=1)
    width = serializers.IntegerField(required=False, min_value=1)

class VideoUploadSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Django de subida de video.
    Mapea contra `analysis_videoupload`.
    """
    video = serializers.FileField(
        write_only=True, 
        required=True,
        error_messages={
            "required": "No video provided", 
            "invalid": "Debes enviar un archivo de video válido."
        }
    )

    class Meta:
        model = VideoUpload
        fields = [
            'idVideoUpload', 'nombreOriginal', 'rutaArchivo', 
            'tamanioBytes', 'estado', 'fechaCarga', 'video'
        ]
        read_only_fields = [
            'idVideoUpload', 'rutaArchivo', 'tamanioBytes', 
            'estado', 'fechaCarga'
        ]
