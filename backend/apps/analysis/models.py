from django.db import models

from apps.users.models import Users


class VideoUpload(models.Model):
    """Registro de videos subidos para procesamiento de análisis."""

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PROCESSING', 'Procesando'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]

    idVideoUpload = models.AutoField(primary_key=True)
    idUsuario = models.ForeignKey(Users, on_delete=models.SET_NULL, db_column='idUsuario', related_name='videos_uploaded', null=True, blank=True)
    idEmpresa = models.IntegerField(null=True, blank=True)  # FK a empresa.idEmpresa (auditoría/tenant)
    nombreOriginal = models.CharField(max_length=255)
    rutaArchivo = models.CharField(max_length=500)
    tamanioBytes = models.BigIntegerField()
    duracionSegundos = models.FloatField(null=True, blank=True)
    fps = models.FloatField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    celeryTaskId = models.CharField(max_length=255, null=True, blank=True)
    fechaCarga = models.DateTimeField(auto_now_add=True)
    fechaProcesamiento = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'analysis_videoupload'
        managed = False
        indexes = [
            models.Index(fields=['estado'], name='ix_video_estado'),
            models.Index(fields=['fechaCarga'], name='ix_video_fechacarga'),
        ]

    def __str__(self):
        return f"{self.idVideoUpload} - {self.nombreOriginal} ({self.estado})"


class DetectionEvent(models.Model):
    """Evento de comportamiento detectado sobre un video."""

    EVENT_TYPES = [
        ('PELEA', 'Pelea'),
        ('DISTURBIO', 'Disturbio'),
        ('NORMAL', 'Normal'),
    ]

    idDetectionEvent = models.AutoField(primary_key=True)
    idVideoUpload = models.ForeignKey(VideoUpload, on_delete=models.CASCADE, db_column='idVideoUpload', related_name='eventos')
    tipoEvento = models.CharField(max_length=20, choices=EVENT_TYPES)
    confianza = models.FloatField()
    frameInicio = models.IntegerField()
    frameFin = models.IntegerField()
    tiempoInicio = models.FloatField()
    tiempoFin = models.FloatField()
    personasInvolucradas = models.IntegerField(default=1)
    detalles = models.JSONField(null=True, blank=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    usuarioCreacion = models.CharField(max_length=100, null=True, blank=True)
    usuarioModificacion = models.CharField(max_length=100, null=True, blank=True)
    fechaModificacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'analysis_detectionevent'
        managed = False
        indexes = [
            models.Index(fields=['idVideoUpload', 'fechaCreacion'], name='ix_event_video_fecha'),
            models.Index(fields=['tipoEvento'], name='ix_event_tipo'),
        ]

    def __str__(self):
        return f"{self.tipoEvento} @ {self.tiempoInicio:.2f}s"


class PersonKeypoints(models.Model):
    """Keypoints de una persona detectada en un frame específico."""

    idPersonKeypoints = models.AutoField(primary_key=True)
    idDetectionEvent = models.ForeignKey(DetectionEvent, on_delete=models.CASCADE, db_column='idDetectionEvent', related_name='keypoints')
    personId = models.IntegerField()
    frameNumber = models.IntegerField()
    keypointsJson = models.JSONField(default=dict)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    usuarioCreacion = models.CharField(max_length=100, null=True, blank=True)
    usuarioModificacion = models.CharField(max_length=100, null=True, blank=True)
    fechaModificacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'analysis_personkeypoints'
        managed = False
        indexes = [
            models.Index(fields=['idDetectionEvent', 'personId'], name='ix_kp_event_person'),
            models.Index(fields=['frameNumber'], name='ix_kp_frame'),
        ]

    def __str__(self):
        return f"Evento {self.idDetectionEvent_id} - Persona {self.personId} - Frame {self.frameNumber}"


class AnalysisReport(models.Model):
    """Reporte consolidado por video procesado."""

    idAnalysisReport = models.AutoField(primary_key=True)
    idVideoUpload = models.OneToOneField(VideoUpload, on_delete=models.CASCADE, db_column='idVideoUpload', related_name='reporte')
    idEmpresa = models.IntegerField(null=True, blank=True)  # FK a empresa.idEmpresa (auditoría/tenant)
    totalFrames = models.IntegerField(default=0)
    totalDuracionSegundos = models.FloatField(default=0)
    totalEventos = models.IntegerField(default=0)
    totalPeleas = models.IntegerField(default=0)
    totalDisturbios = models.IntegerField(default=0)
    confianzaPromedio = models.FloatField(default=0)
    confianzaMaxima = models.FloatField(default=0)
    tiempoProcesamientoSegundos = models.FloatField(null=True, blank=True)
    estadisticas = models.JSONField(null=True, blank=True)
    resumenJson = models.JSONField(null=True, blank=True)
    generadoEn = models.DateTimeField(auto_now_add=True)
    actualizadoEn = models.DateTimeField(auto_now=True)
    usuarioCreacion = models.CharField(max_length=100, null=True, blank=True)
    usuarioModificacion = models.CharField(max_length=100, null=True, blank=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    fechaModificacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'analysis_report'
        managed = False

    def __str__(self):
        return f"Reporte video {self.idVideoUpload_id}"


class SystemParameter(models.Model):
    """Parámetros de sistema para configuración dinámica de análisis (GLOBAL, no por empresa)."""

    TYPE_CHOICES = [
        ('INT', 'Entero'),
        ('FLOAT', 'Decimal'),
        ('STRING', 'Texto'),
        ('BOOL', 'Booleano'),
    ]

    idParameter = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=100, unique=True)
    valor = models.CharField(max_length=500)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TYPE_CHOICES, default='STRING')

    class Meta:
        db_table = 'systemParameter'
        managed = False

    def get_typed_value(self):
        """Convierte el valor al tipo especificado."""
        if self.tipo == 'INT':
            return int(self.valor)
        if self.tipo == 'FLOAT':
            return float(self.valor)
        if self.tipo == 'BOOL':
            return str(self.valor).lower() in ('true', '1', 'yes')
        return self.valor
