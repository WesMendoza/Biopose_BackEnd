from django.db import models

from apps.users.models import Users


class ImageUpload(models.Model):
    """Registro de imágenes subidas para detección de pose estática."""

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PROCESSING', 'Procesando'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]

    idImageUpload = models.AutoField(primary_key=True, db_column='idImageUpload')
    idUsuario = models.ForeignKey(Users, on_delete=models.SET_NULL, db_column='idUsuario', related_name='imagesUploaded', null=True, blank=True)
    idEmpresa = models.IntegerField(null=True, blank=True, db_column='idEmpresa')
    nombreOriginal = models.CharField(max_length=255, db_column='nombreOriginal')
    rutaArchivoOriginal = models.CharField(max_length=500, db_column='rutaArchivoOriginal')
    rutaArchivoProcesado = models.CharField(max_length=500, null=True, blank=True, db_column='rutaArchivoProcesado')
    rutaArchivoJson = models.CharField(max_length=500, null=True, blank=True, db_column='rutaArchivoJson')
    tamanioBytes = models.BigIntegerField(db_column='tamanioBytes')
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_column='estado')
    fechaCarga = models.DateTimeField(auto_now_add=True, db_column='fechaCarga')
    fechaProcesamiento = models.DateTimeField(null=True, blank=True, db_column='fechaProcesamiento')

    class Meta:
        db_table = 'analysisImageUpload'
        managed = False
        indexes = [
            models.Index(fields=['estado'], name='ix_image_estado'),
            models.Index(fields=['fechaCarga'], name='ix_image_fechacarga'),
        ]

    def __str__(self):
        return f"{self.idImageUpload} - {self.nombreOriginal} ({self.estado})"


class VideoUpload(models.Model):
    """Registro de videos subidos para procesamiento de análisis."""

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PROCESSING', 'Procesando'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]

    idVideoUpload = models.AutoField(primary_key=True, db_column='idVideoUpload')
    idUsuario = models.ForeignKey(Users, on_delete=models.SET_NULL, db_column='idUsuario', related_name='videosUploaded', null=True, blank=True)
    idEmpresa = models.IntegerField(null=True, blank=True, db_column='idEmpresa')  # FK a empresa.idEmpresa (auditoría/tenant)
    nombreOriginal = models.CharField(max_length=255, db_column='nombreOriginal')
    rutaArchivo = models.CharField(max_length=500, db_column='rutaArchivo')
    tamanioBytes = models.BigIntegerField(db_column='tamanioBytes')
    duracionSegundos = models.FloatField(null=True, blank=True, db_column='duracionSegundos')
    fps = models.FloatField(null=True, blank=True, db_column='fps')
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_column='estado')
    celeryTaskId = models.CharField(max_length=255, null=True, blank=True, db_column='celeryTaskId')
    fechaCarga = models.DateTimeField(auto_now_add=True, db_column='fechaCarga')
    fechaProcesamiento = models.DateTimeField(null=True, blank=True, db_column='fechaProcesamiento')

    class Meta:
        db_table = 'analysisVideoUpload'
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

    idDetectionEvent = models.AutoField(primary_key=True, db_column='idDetectionEvent')
    idVideoUpload = models.ForeignKey(VideoUpload, on_delete=models.CASCADE, db_column='idVideoUpload', related_name='eventos')
    tipoEvento = models.CharField(max_length=20, choices=EVENT_TYPES, db_column='tipoEvento')
    confianza = models.FloatField(db_column='confianza')
    frameInicio = models.IntegerField(db_column='frameInicio')
    frameFin = models.IntegerField(db_column='frameFin')
    tiempoInicio = models.FloatField(db_column='tiempoInicio')
    tiempoFin = models.FloatField(db_column='tiempoFin')
    personasInvolucradas = models.IntegerField(default=1, db_column='personasInvolucradas')
    detalles = models.JSONField(null=True, blank=True, db_column='detalles')
    fechaCreacion = models.DateTimeField(auto_now_add=True, db_column='fechaCreacion')
    usuarioCreacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuarioCreacion')
    usuarioModificacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuarioModificacion')
    fechaModificacion = models.DateTimeField(null=True, blank=True, db_column='fechaModificacion')

    class Meta:
        db_table = 'analysisDetectionEvent'
        managed = False
        indexes = [
            models.Index(fields=['idVideoUpload', 'fechaCreacion'], name='ix_event_video_fecha'),
            models.Index(fields=['tipoEvento'], name='ix_event_tipo'),
        ]

    def __str__(self):
        return f"{self.tipoEvento} @ {self.tiempoInicio:.2f}s"


class PersonKeypoints(models.Model):
    """Keypoints de una persona detectada en un frame específico."""

    idPersonKeypoints = models.AutoField(primary_key=True, db_column='idPersonKeypoints')
    idDetectionEvent = models.ForeignKey(DetectionEvent, on_delete=models.CASCADE, db_column='idDetectionEvent', related_name='keypoints')
    personId = models.IntegerField(db_column='personId')
    frameNumber = models.IntegerField(db_column='frameNumber')
    keypointsJson = models.JSONField(default=dict, db_column='keypointsJson')
    fechaCreacion = models.DateTimeField(auto_now_add=True, db_column='fechaCreacion')
    usuarioCreacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuarioCreacion')
    usuarioModificacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuarioModificacion')
    fechaModificacion = models.DateTimeField(null=True, blank=True, db_column='fechaModificacion')

    class Meta:
        db_table = 'analysisPersonKeypoints'
        managed = False
        indexes = [
            models.Index(fields=['idDetectionEvent', 'personId'], name='ix_kp_event_person'),
            models.Index(fields=['frameNumber'], name='ix_kp_frame'),
        ]

    def __str__(self):
        return f"Evento {self.idDetectionEvent_id} - Persona {self.personId} - Frame {self.frameNumber}"


class AnalysisReport(models.Model):
    """Reporte consolidado por video procesado."""

    idAnalysisReport = models.AutoField(primary_key=True, db_column='idAnalysisReport')
    idVideoUpload = models.OneToOneField(VideoUpload, on_delete=models.CASCADE, db_column='idVideoUpload', related_name='reporte')
    idEmpresa = models.IntegerField(null=True, blank=True, db_column='idEmpresa')  # FK a empresa.idEmpresa (auditoría/tenant)
    totalFrames = models.IntegerField(default=0, db_column='totalFrames')
    totalDuracionSegundos = models.FloatField(default=0, db_column='totalDuracionSegundos')
    totalEventos = models.IntegerField(default=0, db_column='totalEventos')
    totalPeleas = models.IntegerField(default=0, db_column='totalPeleas')
    totalDisturbios = models.IntegerField(default=0, db_column='totalDisturbios')
    confianzaPromedio = models.FloatField(default=0, db_column='confianzaPromedio')
    confianzaMaxima = models.FloatField(default=0, db_column='confianzaMaxima')
    tiempoProcesamientoSegundos = models.FloatField(null=True, blank=True, db_column='tiempoProcesamientoSegundos')
    estadisticas = models.JSONField(null=True, blank=True, db_column='estadisticas')
    resumenJson = models.JSONField(null=True, blank=True, db_column='resumenJson')
    rutaJsonKeypoints = models.CharField(max_length=500, null=True, blank=True, db_column='rutaJsonKeypoints')
    generadoEn = models.DateTimeField(auto_now_add=True, db_column='generadoEn')
    actualizadoEn = models.DateTimeField(auto_now=True, db_column='actualizadoEn')
    usuarioCreacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuarioCreacion')
    usuarioModificacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuarioModificacion')
    fechaCreacion = models.DateTimeField(auto_now_add=True, db_column='fechaCreacion')
    fechaModificacion = models.DateTimeField(null=True, blank=True, db_column='fechaModificacion')

    class Meta:
        db_table = 'analysisReport'
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
