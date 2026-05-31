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

    idVideoUpload = models.AutoField(primary_key=True, db_column='idvideoupload')
    idUsuario = models.ForeignKey(Users, on_delete=models.SET_NULL, db_column='idusuario', related_name='videos_uploaded', null=True, blank=True)
    idEmpresa = models.IntegerField(null=True, blank=True, db_column='idempresa')  # FK a empresa.idEmpresa (auditoría/tenant)
    nombreOriginal = models.CharField(max_length=255, db_column='nombreoriginal')
    rutaArchivo = models.CharField(max_length=500, db_column='rutaarchivo')
    tamanioBytes = models.BigIntegerField(db_column='tamaniobytes')
    duracionSegundos = models.FloatField(null=True, blank=True, db_column='duracionsegundos')
    fps = models.FloatField(null=True, blank=True, db_column='fps')
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_column='estado')
    celeryTaskId = models.CharField(max_length=255, null=True, blank=True, db_column='celerytaskid')
    fechaCarga = models.DateTimeField(auto_now_add=True, db_column='fechacarga')
    fechaProcesamiento = models.DateTimeField(null=True, blank=True, db_column='fechaprocesamiento')

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

    idDetectionEvent = models.AutoField(primary_key=True, db_column='iddetectionevent')
    idVideoUpload = models.ForeignKey(VideoUpload, on_delete=models.CASCADE, db_column='idvideoupload', related_name='eventos')
    tipoEvento = models.CharField(max_length=20, choices=EVENT_TYPES, db_column='tipoevento')
    confianza = models.FloatField(db_column='confianza')
    frameInicio = models.IntegerField(db_column='frameinicio')
    frameFin = models.IntegerField(db_column='framefin')
    tiempoInicio = models.FloatField(db_column='tiempoinicio')
    tiempoFin = models.FloatField(db_column='tiempofin')
    personasInvolucradas = models.IntegerField(default=1, db_column='personasinvolucradas')
    detalles = models.JSONField(null=True, blank=True, db_column='detalles')
    fechaCreacion = models.DateTimeField(auto_now_add=True, db_column='fechacreacion')
    usuarioCreacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuariocreacion')
    usuarioModificacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuariomodificacion')
    fechaModificacion = models.DateTimeField(null=True, blank=True, db_column='fechamodificacion')

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

    idPersonKeypoints = models.AutoField(primary_key=True, db_column='idpersonkeypoints')
    idDetectionEvent = models.ForeignKey(DetectionEvent, on_delete=models.CASCADE, db_column='iddetectionevent', related_name='keypoints')
    personId = models.IntegerField(db_column='personid')
    frameNumber = models.IntegerField(db_column='framenumber')
    keypointsJson = models.JSONField(default=dict, db_column='keypointsjson')
    fechaCreacion = models.DateTimeField(auto_now_add=True, db_column='fechacreacion')
    usuarioCreacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuariocreacion')
    usuarioModificacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuariomodificacion')
    fechaModificacion = models.DateTimeField(null=True, blank=True, db_column='fechamodificacion')

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

    idAnalysisReport = models.AutoField(primary_key=True, db_column='idanalysisreport')
    idVideoUpload = models.OneToOneField(VideoUpload, on_delete=models.CASCADE, db_column='idvideoupload', related_name='reporte')
    idEmpresa = models.IntegerField(null=True, blank=True, db_column='idempresa')  # FK a empresa.idEmpresa (auditoría/tenant)
    totalFrames = models.IntegerField(default=0, db_column='totalframes')
    totalDuracionSegundos = models.FloatField(default=0, db_column='totalduracionsegundos')
    totalEventos = models.IntegerField(default=0, db_column='totaleventos')
    totalPeleas = models.IntegerField(default=0, db_column='totalpeleas')
    totalDisturbios = models.IntegerField(default=0, db_column='totaldisturbios')
    confianzaPromedio = models.FloatField(default=0, db_column='confianzapromedio')
    confianzaMaxima = models.FloatField(default=0, db_column='confianzamaxima')
    tiempoProcesamientoSegundos = models.FloatField(null=True, blank=True, db_column='tiempoprocesamientosegundos')
    estadisticas = models.JSONField(null=True, blank=True, db_column='estadisticas')
    resumenJson = models.JSONField(null=True, blank=True, db_column='resumenjson')
    generadoEn = models.DateTimeField(auto_now_add=True, db_column='generadoen')
    actualizadoEn = models.DateTimeField(auto_now=True, db_column='actualizadoen')
    usuarioCreacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuariocreacion')
    usuarioModificacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuariomodificacion')
    fechaCreacion = models.DateTimeField(auto_now_add=True, db_column='fechacreacion')
    fechaModificacion = models.DateTimeField(null=True, blank=True, db_column='fechamodificacion')

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
