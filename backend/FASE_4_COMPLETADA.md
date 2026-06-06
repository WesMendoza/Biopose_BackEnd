# FASE 4: Procesamiento Asíncrono (EN PROGRESO)

Esta fase se enfoca en desvincular el procesamiento de video (pesado) del ciclo de vida de la petición HTTP, delegando el trabajo a un sistema de colas (Celery) respaldado por Redis. Además, se aplican estrategias de optimización para reducir drásticamente el consumo de recursos de los modelos de IA (YOLO y LSTM).

## 1. Tareas de Optimización de Modelos y Estrategia Visual
Se modificó `backend/services/video_processor.py` para incluir:
- **Frame Skipping**: Solo se procesan `n` frames por segundo según el parámetro indicado (por defecto 1 de cada 5).
- **Lectura Secuencial**: Uso de `capture.read()` en iteración en vez de costosos accesos aleatorios `capture.set()`.
- **Downscaling**: Redimensionamiento a `640x640` previo a procesamiento.
- **Motion Gating**: Uso de `cv2.createBackgroundSubtractorMOG2()` para ignorar por completo el procesamiento YOLO/LSTM en frames donde no existe movimiento (ej. habitaciones vacías).
- **Renderizado Vectorial en Cliente (JSON + Canvas)**: En lugar de renderizar y guardar un nuevo video mp4 procesado pesado, el backend procesa de forma vectorial los keypoints (usando Batching) y almacena las coordenadas en un archivo JSON ligero. Este JSON se guarda en el servidor y su ruta se registra en la base de datos (`rutaJsonKeypoints` en `AnalysisReport`). El frontend es el encargado de leer este JSON y dibujar los esqueletos sobre el video usando HTML5 Canvas, ahorrando recursos de CPU y almacenamiento.

Nota operativa: el flujo de video sí usa YOLO sobre frames muestreados para extraer keypoints y luego alimenta el clasificador LSTM. La novedad es que los keypoints se extraen como una serie de vectores JSON y se exponen listos para renderizado web.

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

## 4. Flujo Real de Prueba en Postman

Para validar la carga y el procesamiento de video con el entorno actual, el flujo debe ejecutarse en este orden:

1. **Subir el video**
	- **POST** `/api/analysis/media/videos/upload/`
	- Archivo esperado en `form-data`: `video`
	- Método involucrado: `VideoUploadView.post()` en `backend/apps/analysis/api/media/views.py`
	- Efecto: guarda el archivo en `backend/media/videos/uploads/` y crea el registro `VideoUpload` en BD con estado `PENDING`

2. **Lanzar el procesamiento**
	- **POST** `/api/analysis/videos/{video_id}/process/`
	- Métodos involucrados:
	  - `ProcessVideoView.post()` en `backend/apps/analysis/api/behavior/views.py`
	  - `process_video_task.delay()` en `backend/apps/analysis/tasks.py`
	  - `analyze_video_behavior()` en `backend/services/video_processor.py`
	- Parámetros opcionales en JSON:
	  - `mode`: `operativo` | `analitico` | `debug`
	  - `dimension`: `2D` | `3D`
	  - `fps_skip`: entero mayor o igual a 1
	  - `confidence_threshold`: decimal entre 0 y 1
	- Efecto: cambia el estado a `PROCESSING`, envía la tarea a Celery y retorna `202 Accepted`

3. **Consultar resultados**
	- **GET** `/api/analysis/videos/{video_id}/results/`
	- Método involucrado: `VideoResultsView.get()` en `backend/apps/analysis/api/behavior/views.py`
	- Efecto: devuelve el resumen final cuando el video ya está `COMPLETED`, o `202` si sigue en proceso
	- Nota operativa: en la implementación actual no existe un endpoint de progreso incremental; "consultar progreso luego" significa repetir esta consulta cada pocos segundos hasta que el estado cambie o el reporte esté disponible.

## 5. Métodos Técnicos Involucrados

Este es el recorrido interno que debe quedar validado durante la prueba:

- `VideoUploadView.post()` valida el archivo, lo guarda en disco y registra `VideoUpload`.
- `ProcessVideoView.post()` valida el `video_id`, lee parámetros de análisis y encola `process_video_task`.
- `process_video_task()` marca el video como `PROCESSING`, invoca `analyze_video_behavior()` y persiste `AnalysisReport`.
- `analyze_video_behavior()` ejecuta la lógica optimizada de video que usa `frame skipping`, `downscaling`, `motion gating` y detección de keypoints en frames muestreados.
- `VideoResultsView.get()` lee `AnalysisReport` y expone el resultado consolidado para consumo desde Postman.

## 6. Estado del Entorno de Prueba

- Redis ya está levantado en Docker con el contenedor `biopose-redis`.
- Para completar la validación falta levantar el worker de Celery y ejecutar la secuencia anterior desde Postman.
- Comando correcto en Windows: entrar a `backend/` y ejecutar `celery -A core worker -l info --pool=solo` desde ese directorio. Si se corre desde la raíz del repo aparece el error `The module core was not found`.

## 7. Lectura de la Respuesta 404 en `/results/`

Si el endpoint devuelve `{"message": "Reporte no encontrado, pero el video está como COMPLETED. Estado inconsistente."}`, la lectura correcta es esta:

- El registro `VideoUpload` ya pasó a `COMPLETED`.
- El `AnalysisReport` no existe o no quedó persistido en la misma base de datos que está consultando la API.
- El problema no está en el `GET /results/` como tal, sino en la ejecución previa de `process_video_task()` o en la sincronización del worker/BD.

En ese caso, la verificación inmediata debe hacerse en este orden:

1. Revisar el log del worker de Celery.
2. Confirmar que la tarea `process_video_task` terminó sin excepción.
3. Verificar que el reporte fue insertado en `analysisReport`.
4. Revisar que el worker y la API apunten a la misma base de datos.

## 8. Aclaración de alcance del módulo

El endpoint de video no reemplaza al endpoint de pose de imagen. Hoy existen dos caminos distintos:

- `POST /api/analysis/pose/image/<image_id>/process/` para detectar keypoints sobre una imagen ya cargada.
- `POST /api/analysis/videos/{video_id}/process/` para analizar comportamiento de video usando frames muestreados, keypoints intermedios y clasificación LSTM.

Para revisar visualmente cada frame, en lugar de descargar un video procesado pesadísimo o guardar capturas, el API expone la ruta del JSON generado de los keypoints vectoriales en el `AnalysisReport`, el cual el cliente frontend usará para redibujarlos sobre el video original en vivo usando un `<canvas>`.
