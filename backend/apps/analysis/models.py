from django.db import models
from apps.users.models import Users

class VideoUpload(models.Model):
    """
    Modelo para registrar videos subidos al sistema.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente de procesamiento'),
        ('PROCESSING', 'En procesamiento'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Falló'),
    ]

    idVideoUpload = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Users, on_delete=models.DO_NOTHING, null=True, blank=True)
    nombreOriginal = models.CharField(max_length=255)
    rutaArchivo = models.CharField(max_length=500)
    tamanio = models.BigIntegerField()  # En bytes
    duracion = models.FloatField(null=True, blank=True)  # En segundos
    fps = models.FloatField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    celeryTaskId = models.CharField(max_length=255, null=True, blank=True)
    fechaCarga = models.DateTimeField(auto_now_add=True)
    fechaProcesamiento = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'videoUpload'
        managed = False


class DetectionEvent(models.Model):
    """
    Modelo para registrar eventos de comportamiento detectados.
    """
    EVENT_TYPES = [
        ('PELEA', 'Pelea/Violencia'),
        ('DISTURBIO', 'Disturbio/Protesta'),
        ('NEUTRAL', 'Comportamiento neutral'),
        ('CAIDA', 'Caída detectada'),
        ('COMPORTAMIENTO_ERRÁTICO', 'Comportamiento errático'),
    ]

    idDetectionEvent = models.AutoField(primary_key=True)
    video = models.ForeignKey(VideoUpload, on_delete=models.CASCADE, related_name='eventos')
    tipoEvento = models.CharField(max_length=50, choices=EVENT_TYPES)
    tiempoInicio = models.FloatField()  # Segundos desde inicio del video
    tiempoFin = models.FloatField(null=True, blank=True)
    duracion = models.FloatField(null=True, blank=True)
    confianza = models.FloatField()  # Probabilidad (0-1)
    personasInvolucradas = models.IntegerField(default=1)
    detalles = models.JSONField(null=True, blank=True)  # Información adicional como keypoints, etc
    fechaCreacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'detectionEvent'
        managed = False


class AnalysisReport(models.Model):
    """
    Modelo para generar reportes consolidados de análisis.
    """
    idAnalysisReport = models.AutoField(primary_key=True)
    video = models.OneToOneField(VideoUpload, on_delete=models.CASCADE, related_name='reporte')
    totalEventos = models.IntegerField(default=0)
    eventosMasComunes = models.JSONField(null=True, blank=True)  # {"PELEA": 5, "DISTURBIO": 3}
    tiempoPromedioProcesamiento = models.FloatField(null=True, blank=True)  # Segundos
    estadisticas = models.JSONField(null=True, blank=True)
    resumenJson = models.JSONField(null=True, blank=True)
    generadoEn = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analysisReport'
        managed = False


class SystemParameter(models.Model):
    """
    Modelo para parámetros configurables del sistema de detección.
    """
    idParameter = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=100, unique=True)
    valor = models.CharField(max_length=500)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=[('INT', 'Entero'), ('FLOAT', 'Decimal'), ('STRING', 'Texto'), ('BOOL', 'Booleano')])

    class Meta:
        db_table = 'systemParameter'
        managed = False

    def get_typed_value(self):
        """Retorna el valor con su tipo correcto."""
        if self.tipo == 'INT':
            return int(self.valor)
        elif self.tipo == 'FLOAT':
            return float(self.valor)
        elif self.tipo == 'BOOL':
            return self.valor.lower() in ('true', '1', 'yes')
        return self.valor
