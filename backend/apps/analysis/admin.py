from django.contrib import admin

from .models import AnalysisReport, DetectionEvent, PersonKeypoints, VideoUpload


@admin.register(VideoUpload)
class VideoUploadAdmin(admin.ModelAdmin):
	list_display = ('idVideoUpload', 'nombreOriginal', 'estado', 'idUsuario', 'fechaCarga')
	list_filter = ('estado', 'fechaCarga')
	search_fields = ('nombreOriginal', 'rutaArchivo', 'celeryTaskId')
	readonly_fields = ('fechaCarga', 'fechaProcesamiento')


@admin.register(DetectionEvent)
class DetectionEventAdmin(admin.ModelAdmin):
	list_display = ('idDetectionEvent', 'idVideoUpload', 'tipoEvento', 'confianza', 'tiempoInicio', 'tiempoFin', 'fechaCreacion')
	list_filter = ('tipoEvento', 'fechaCreacion')
	search_fields = ('idVideoUpload__nombreOriginal',)
	readonly_fields = ('fechaCreacion',)


@admin.register(PersonKeypoints)
class PersonKeypointsAdmin(admin.ModelAdmin):
	list_display = ('idPersonKeypoints', 'idDetectionEvent', 'personId', 'frameNumber', 'fechaCreacion')
	list_filter = ('fechaCreacion',)
	search_fields = ('idDetectionEvent__idVideoUpload__nombreOriginal',)
	readonly_fields = ('fechaCreacion',)


@admin.register(AnalysisReport)
class AnalysisReportAdmin(admin.ModelAdmin):
	list_display = ('idAnalysisReport', 'idVideoUpload', 'totalEventos', 'confianzaPromedio', 'confianzaMaxima', 'generadoEn')
	search_fields = ('idVideoUpload__nombreOriginal',)
	readonly_fields = ('generadoEn', 'actualizadoEn')
