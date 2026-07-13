from celery import shared_task
from django.utils import timezone
from .models import VideoUpload, AnalysisReport
import os
import json
from django.conf import settings

def _resolve_media_path(stored_path):
    if not stored_path:
        return stored_path
    if os.path.isabs(stored_path):
        return stored_path
    return os.path.join(settings.MEDIA_ROOT, stored_path)

@shared_task(bind=True)
def process_video_task(self, video_id, mode='operativo', dimension='2D', fps_skip=5, confidence_threshold=0.75, analysis_type='multipersona'):
    try:
        video_upload = VideoUpload.objects.get(idVideoUpload=video_id)
        video_upload.estado = 'PROCESSING'
        video_upload.celeryTaskId = self.request.id
        video_upload.save(update_fields=['estado', 'celeryTaskId'])

        from services.video_processor import analyze_video_individual, analyze_video_multipersona
        absolute_video_path = os.path.join(settings.MEDIA_ROOT, str(video_upload.rutaArchivo))

        if analysis_type == 'individual':
            resultado = analyze_video_individual(
                video_path=absolute_video_path,
                mode=mode,
                dimension=dimension,
                fps_skip=fps_skip,
                confidence_threshold=confidence_threshold
            )
        else:
            resultado = analyze_video_multipersona(
                video_path=absolute_video_path,
                mode=mode,
                dimension=dimension,
                fps_skip=fps_skip,
                confidence_threshold=confidence_threshold
            )

        # 1. CREAMOS EL ARCHIVO JSON FÍSICO TEMPORALMENTE
        report_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(report_dir, exist_ok=True)
        json_filename = f'keypoints_video_{video_id}.json'
        json_path = os.path.join(report_dir, json_filename)
        
        with open(json_path, 'w') as f:
            json.dump({
                'frames': resultado.get('frames_data', []),  # <--- AQUÍ PASAMOS TODOS LOS FRAMES MULTIPERSONA
                'detections': resultado.get('detections', [])
            }, f)
        
        ruta_json_relativa = f'reports/{json_filename}'

        # 2. GUARDAMOS EL REPORTE EN DB
        reporte = AnalysisReport.objects.create(
            idVideoUpload=video_upload,
            idEmpresa=video_upload.idEmpresa,
            totalFrames=resultado.get('total_frames', 0),
            totalDuracionSegundos=resultado.get('duration_seconds', 0.0),
            totalEventos=len(resultado.get('detections', [])),
            totalPeleas=resultado.get('summary', {}).get('detections_by_type', {}).get('PELEAR', 0),
            totalDisturbios=resultado.get('summary', {}).get('detections_by_type', {}).get('DISTURBIO', 0),
            confianzaPromedio=resultado.get('summary', {}).get('average_confidence', 0.0),
            confianzaMaxima=resultado.get('summary', {}).get('max_confidence', 0.0),
            tiempoProcesamientoSegundos=resultado.get('processing_time_seconds', 0.0),
            estadisticas=resultado.get('summary', {}),
            rutaJsonKeypoints=ruta_json_relativa,
            usuarioCreacion='Sistema'
        )

        video_upload.estado = 'COMPLETED'
        video_upload.fechaProcesamiento = timezone.now()
        video_upload.save(update_fields=['estado', 'fechaProcesamiento'])

        return {'status': 'COMPLETED', 'video_id': video_id, 'report_id': reporte.idAnalysisReport}

    except VideoUpload.DoesNotExist:
        return {'status': 'FAILED', 'error': f'Video no existe.'}
    except Exception as e:
        try:
            video_upload = VideoUpload.objects.get(idVideoUpload=video_id)
            video_upload.estado = 'FAILED'
            video_upload.save(update_fields=['estado'])
        except: pass
        return {'status': 'FAILED', 'error': str(e)}

@shared_task
def cleanup_orphaned_media_task():
    """
    Escanea la base de datos buscando archivos multimedia (VideoUpload e ImageUpload)
    que tengan más de 1 hora de antigüedad y los elimina físicamente del disco
    junto con sus reportes JSON asociados y el registro en la BD, para evitar acumulación.
    """
    from datetime import timedelta
    from .models import VideoUpload, ImageUpload
    import os
    
    time_threshold = timezone.now() - timedelta(hours=1)
    
    # Limpiar Videos
    old_videos = VideoUpload.objects.filter(fechaCreacion__lt=time_threshold)
    for video in old_videos:
        try:
            if video.rutaArchivo:
                video_path = os.path.join(settings.MEDIA_ROOT, str(video.rutaArchivo))
                if os.path.exists(video_path): os.remove(video_path)
            
            if video.rutaVideoProcesado:
                proc_path = os.path.join(settings.MEDIA_ROOT, str(video.rutaVideoProcesado))
                if os.path.exists(proc_path): os.remove(proc_path)
            
            # Borrar JSON asociado
            json_filename = f'keypoints_video_{video.idVideoUpload}.json'
            json_path = os.path.join(settings.MEDIA_ROOT, 'reports', json_filename)
            if os.path.exists(json_path): os.remove(json_path)
            
            video.delete()
        except Exception as e:
            print(f"Error limpiando video {video.idVideoUpload}: {e}")

    # Limpiar Imágenes
    old_images = ImageUpload.objects.filter(fechaCreacion__lt=time_threshold)
    for image in old_images:
        try:
            if image.rutaArchivoOriginal:
                orig_path = os.path.join(settings.MEDIA_ROOT, str(image.rutaArchivoOriginal))
                if os.path.exists(orig_path): os.remove(orig_path)
                
            if image.rutaArchivoProcesado:
                proc_path = os.path.join(settings.MEDIA_ROOT, str(image.rutaArchivoProcesado))
                if os.path.exists(proc_path): os.remove(proc_path)
                
            if image.rutaArchivoJson:
                json_path = os.path.join(settings.MEDIA_ROOT, str(image.rutaArchivoJson))
                if os.path.exists(json_path): os.remove(json_path)
                
            image.delete()
        except Exception as e:
            print(f"Error limpiando imagen {image.idImageUpload}: {e}")

    return "Limpieza de huérfanos completada."