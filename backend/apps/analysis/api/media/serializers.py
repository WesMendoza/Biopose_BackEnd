from rest_framework import serializers
from apps.analysis.models import VideoUpload, ImageUpload

class ImageUploadSerializer(serializers.ModelSerializer):
    """
    Serializer nativo para validar cargas de imágenes aisladas, asociado al modelo ImageUpload.
    """
    image = serializers.ImageField(
        write_only=True,
        required=True,
        error_messages={
            "required": "No image provided", 
            "invalid": "Debes enviar un archivo de imagen válido."
        }
    )

    class Meta:
        model = ImageUpload
        fields = [
            'idImageUpload', 'nombreOriginal', 'rutaArchivoOriginal', 
            'rutaArchivoProcesado', 'tamanioBytes', 'estado', 'fechaCarga', 'image'
        ]
        read_only_fields = [
            'idImageUpload', 'nombreOriginal', 'rutaArchivoOriginal', 'rutaArchivoProcesado',
            'tamanioBytes', 'estado', 'fechaCarga'
        ]

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
            'idVideoUpload', 'nombreOriginal', 'rutaArchivo', 'tamanioBytes', 
            'estado', 'fechaCarga'
        ]
