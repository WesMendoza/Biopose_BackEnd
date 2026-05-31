from rest_framework import serializers

class KeypointSerializer(serializers.Serializer):
    """
    Representa un único punto anatómico detectado por YOLO (COCO format).
    """
    id = serializers.IntegerField(help_text="ID del keypoint (0-16 en formato COCO)")
    name = serializers.CharField(help_text="Nombre anatómico (ej: 'nose', 'left_eye')")
    x = serializers.FloatField(help_text="Coordenada X absoluta en píxeles")
    y = serializers.FloatField(help_text="Coordenada Y absoluta en píxeles")
    confidence = serializers.FloatField(help_text="Nivel de confianza de la detección (0.0 a 1.0)")

class BoundingBoxSerializer(serializers.Serializer):
    """
    Representa la caja delimitadora donde se encontró a la persona.
    """
    x1 = serializers.IntegerField()
    y1 = serializers.IntegerField()
    x2 = serializers.IntegerField()
    y2 = serializers.IntegerField()

class PersonPoseSerializer(serializers.Serializer):
    """
    Representa a una persona detectada con sus 17 puntos clave (si es 2D).
    """
    person_id = serializers.IntegerField(help_text="ID secuencial de la persona detectada en el frame")
    bbox = BoundingBoxSerializer()
    keypoints = KeypointSerializer(many=True)

class PoseDetectionResponseSerializer(serializers.Serializer):
    """
    Estructura de respuesta exitosa tras procesar una imagen mediante YOLO.
    """
    success = serializers.BooleanField(default=True)
    model_used = serializers.CharField()
    position = serializers.CharField(help_text="Clasificación global de la pose en base al aspect ratio (ej: horizontal, cuadrada, vertical)")
    persons_detected = serializers.IntegerField()
    persons = PersonPoseSerializer(many=True)
