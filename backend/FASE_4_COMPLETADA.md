# FASE 4: Procesamiento Asíncrono (EN PROGRESO)

Esta fase se enfoca en desvincular el procesamiento de video (pesado) del ciclo de vida de la petición HTTP, delegando el trabajo a un sistema de colas (Celery) respaldado por Redis. Además, se aplican estrategias de optimización para reducir drásticamente el consumo de recursos de los modelos de IA (YOLO y LSTM).

## 1. Tareas de Optimización de Modelos Completadas
Se modificó `backend/services/video_processor.py` para incluir:
- **Frame Skipping**: Solo se procesan `n` frames por segundo según el parámetro indicado (por defecto 1 de cada 5).
- **Lectura Secuencial**: Uso de `capture.read()` en iteración en vez de costosos accesos aleatorios `capture.set()`.
- **Downscaling**: Redimensionamiento a `640x640` previo a procesamiento.
- **Motion Gating**: Uso de `cv2.createBackgroundSubtractorMOG2()` para ignorar por completo el procesamiento YOLO/LSTM en frames donde no existe movimiento (ej. habitaciones vacías).

## 2. Integración con Celery y Redis
- Creado `backend/core/celery.py` y registrado en `__init__.py`.
- Configuradas las URLs de `CELERY_BROKER_URL` y `CELERY_RESULT_BACKEND` en `settings.py`.
- Creado archivo `backend/apps/analysis/tasks.py` que incluye la tarea `@shared_task process_video_task`. Esta tarea actualiza el estado del video a `PROCESSING`, ejecuta el modelo optimizado, persiste el reporte y lo marca como `COMPLETED`.

## 3. Endpoints Implementados (Módulo Behavior)

### Iniciar Procesamiento Asíncrono
**POST** `/api/analysis/videos/{video_id}/process/`

### Consultar Resultados
**GET** `/api/analysis/videos/{video_id}/results/`

*(Nota: Faltan las pruebas manuales o automatizadas, levantar un worker de Celery local, y probar el SSE para progreso en vivo de la Fase 4/5).*
