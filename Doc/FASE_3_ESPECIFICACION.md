# 📋 FASE 3: Endpoints REST Básicos - ESPECIFICACIÓN DETALLADA

**Estado**: ⏳ Pendiente (Análisis Completado)  
**Basado en**: Análisis de código legacy en `Tesis/src/`  
**Objetivo**: Exponer servicios de IA a través de REST API y cubrir flujos legacy de carga/procesamiento

---

## 1. CONTEXTO DEL CÓDIGO LEGACY

El sistema actual en `Tesis/src/main.py` implementa **37 endpoints Flask** distribuidos en 8 grupos funcionales.

### 1.1 Flujos Clave Identificados

#### **Flujo 1: Subida y Análisis de Imágenes**
```
Usuario → POST /upload (imagen)
  ↓
YOLOv8s-pose detecta keypoints (17 puntos)
  ↓
POST /save → Persiste imagen + keypoints a BD
  ↓
Respuesta JSON con posición de cuerpo (horizontal/vertical/cuadrada)
```

**Endpoints Legacy**:
- `POST /upload` - Procesa imagen con YOLO, retorna 17 keypoints
- `POST /resize_image` - Redimensiona imagen (multipart form)
- `POST /resize_image_params` - Redimensiona con parámetros específicos
- `POST /save` - Persiste imagen + keypoints en BD
- `POST /upload_image_video` - Variante para imágenes extraídas de videos
- `POST /save_image_from_video` - Persiste imagen del flujo de video

#### **Flujo 2: Subida y Procesamiento de Videos LSTM**
```
Usuario → POST /save-video-lstm (video)
  ↓
POST /process-video → Inicia análisis de comportamiento
  ↓
GET /stream_frames_lstm/<filename>/<mode> → Streaming eventos + frames
  ↓
GET /results-video-lstm/<filename> → Eventos consolidados
```

**Endpoints Legacy**:
- `POST /save-video-lstm` - Guarda video en directorio temporal
- `POST /process-video` - Inicia análisis con LSTM (comportamiento)
- `GET /stream_frames_lstm/<filename>/<mode>/<dimension>` - Server-Sent Events con progreso
- `GET /results-video-lstm/<filename>` - Detecciones consolidadas
- `GET /processed-video-lstm/<filename>` - Descarga video procesado (WebM/MP4)

#### **Flujo 3: Generación de Frames desde Video**
```
Usuario → POST /generate_images_from_videos (video, fps)
  ↓
Extrae frames según FPS configurado (máx 30 seg)
  ↓
Retorna array de imágenes en base64
```

---

## 2. ESPECIFICACIÓN DE ENDPOINTS DJANGO

> **Nota:** Todos estos endpoints se pueden visualizar y probar de forma interactiva a través de **Swagger UI** ingresando a `/api/docs/` en tu servidor de desarrollo.

### 2.1 GESTIÓN DE IMÁGENES

#### **2.1.1 Subir y Procesar Imagen**
```
POST /api/analysis/images/upload/

Content-Type: multipart/form-data
Body:
  - image: (binary file)
  - width: (optional, int)
  - height: (optional, int)

Response 200:
{
  "id": 123,
  "message": "Imagen procesada exitosamente.",
  "filename": "image_20260503_143045.jpg",
  "path": "media/images/uploads/image_20260503_143045.jpg",
  "image_position": "horizontal|vertical|cuadrada",
  "keypoints": [
    {"id": 0, "name": "nose", "x": 100.5, "y": 200.3, "z": 0, "confidence": 0.98},
    {"id": 1, "name": "left_eye", "x": 95.2, "y": 180.1, "z": 0, "confidence": 0.97},
    ...17 total keypoints (COCO formato)
  ],
  "image_dimensions": {
    "original_width": 1920,
    "original_height": 1080,
    "processed_width": 640,
    "processed_height": 480
  },
  "processing_time_ms": 1250,
  "model": "yolov8s-pose"
}

Response 400:
{
  "error": "No image provided",
  "message": "Debes enviar un archivo de imagen válido."
}

Response 500:
{
  "error": "Processing failed",
  "message": "Error al procesar imagen: {detalle}"
}
```

**Notas**:
- Soporta: JPEG, PNG
- Máximo tamaño: 50MB (heredado de legacy)
- Detecta posición automáticamente basada en dimensiones

---

#### **2.1.2 Redimensionar Imagen**
```
POST /api/analysis/images/resize/

Content-Type: multipart/form-data
Body:
  - image: (binary file)
  - width: (int, required)
  - height: (int, required)

Response 200:
{
  "message": "Imagen redimensionada exitosamente.",
  "filename": "image_resized_20260503_143045.jpg",
  "path": "media/images/processed/image_resized_20260503_143045.jpg",
  "new_dimensions": {
    "width": 640,
    "height": 480
  },
  "original_dimensions": {
    "width": 1920,
    "height": 1080
  }
}

Response 400:
{
  "error": "Invalid parameters",
  "message": "width y height deben ser números positivos."
}
```

---

#### **2.1.3 Guardar Imagen con Keypoints**
```
POST /api/analysis/images/save/

Content-Type: application/json
Body:
{
  "image_id": 123,
  "keypoints": [
    {"id": 0, "x": 100.5, "y": 200.3, "z": 0},
    ...17 keypoints
  ],
  "image_metadata": {
    "width": 640,
    "height": 480,
    "position": "horizontal",
    "source": "user_upload|video_extraction"
  }
}

Response 200:
{
  "success": true,
  "message": "Imagen y keypoints guardados exitosamente.",
  "image_id": 123,
  "created_at": "2026-05-03T14:30:45Z",
  "storage_path": "media/images/processed/image_20260503_143045.jpg"
}

Response 400:
{
  "success": false,
  "message": "Campos requeridos incompletos."
}
```

---

### 2.2 GESTIÓN DE VIDEOS

#### **2.2.1 Subir Video**
```
POST /api/analysis/videos/upload/

Content-Type: multipart/form-data
Body:
  - video: (binary file)
  - description: (optional, string)

Response 200:
{
  "id": 456,
  "filename": "video_20260503_143045.mp4",
  "original_filename": "surveillance_day1.mp4",
  "path": "media/videos/uploads/video_20260503_143045.mp4",
  "size_bytes": 1048576000,
  "duration_seconds": 300.5,
  "status": "uploaded",
  "created_at": "2026-05-03T14:30:45Z"
}

Response 400:
{
  "error": "No video provided",
  "message": "Debes enviar un archivo de video válido."
}

Response 413:
{
  "error": "File too large",
  "message": "El archivo excede el tamaño máximo permitido (50MB)."
}
```

---

#### **2.2.2 Procesar Video (LSTM - Detección de Comportamiento)**
```
POST /api/analysis/videos/{video_id}/process/

Content-Type: application/json
Body:
{
  "mode": "operativo|analitico|debug",
  "dimension": "2D|3D",
  "fps_skip": 5,
  "confidence_threshold": 0.75
}

Response 202 (Procesando):
{
  "id": 456,
  "status": "processing",
  "task_id": "celery-task-uuid-12345",
  "message": "Video en procesamiento. Puedes consultar progreso en /api/analysis/videos/{video_id}/stream/",
  "started_at": "2026-05-03T14:30:45Z"
}

Response 400:
{
  "error": "Invalid parameters",
  "message": "mode debe ser: operativo, analitico o debug."
}

Response 404:
{
  "error": "Video not found",
  "message": "El video con ID {video_id} no existe."
}
```

**Modos de Procesamiento**:
- **operativo**: Solo bounding box + etiqueta de evento (rendimiento máximo)
- **analitico**: Bounding box + esqueleto de pose + etiqueta (balance)
- **debug**: Debug completo con telemetría LSTM, detalle de ventanas, scores internos

---

#### **2.2.3 Stream de Progreso (Server-Sent Events)**
```
GET /api/analysis/videos/{video_id}/stream/?mode=operativo&dimension=2D

Response: text/event-stream
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: progress
data: {
  "video_id": 456,
  "progress_percent": 45,
  "current_frame": 450,
  "total_frames": 1000,
  "processing_time_elapsed_sec": 120,
  "eta_seconds": 147,
  "timestamp": "2026-05-03T14:31:45Z"
}

event: detection
data: {
  "frame_index": 123,
  "timestamp_sec": 12.5,
  "detections": [
    {
      "tipo_evento": "PELEAR",
      "confianza": 0.92,
      "numero_personas": 2,
      "inicio_ventana_frame": 100,
      "fin_ventana_frame": 125,
      "bounding_boxes": [
        {"x1": 100, "y1": 150, "x2": 300, "y2": 600, "person_id": 0},
        {"x1": 350, "y1": 160, "x2": 550, "y2": 620, "person_id": 1}
      ]
    }
  ],
  "frame_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}

event: completed
data: {
  "video_id": 456,
  "status": "completed",
  "total_detections": 15,
  "total_processing_time_sec": 267,
  "detections_summary": {
    "PELEAR": 8,
    "DISTURBIO": 5,
    "NEUTRAL": 2
  }
}

event: error
data: {
  "error": "Processing failed",
  "message": "Error al procesar frame: {detalle}",
  "frame_index": 450
}
```

---

#### **2.2.4 Obtener Resultados (Detecciones Consolidadas)**
```
GET /api/analysis/videos/{video_id}/results/

Response 200:
{
  "id": 456,
  "filename": "video_20260503_143045.mp4",
  "status": "completed|processing|failed",
  "processing_mode": "operativo",
  "total_frames": 1000,
  "duration_seconds": 300.5,
  "processing_time_seconds": 267,
  "detections": [
    {
      "id": 1,
      "tipo_evento": "PELEAR",
      "inicio_segundo": 12.5,
      "fin_segundo": 25.3,
      "duracion_segundos": 12.8,
      "confianza_maxima": 0.95,
      "numero_personas": 2,
      "frames_rango": [125, 253],
      "imagen_evento": "media/videos/results/event_001_PELEAR.jpg",
      "metadata": {
        "bounding_boxes_inicio": [...],
        "bounding_boxes_fin": [...],
        "keypoints_personas": [...]
      }
    },
    {
      "id": 2,
      "tipo_evento": "DISTURBIO",
      "inicio_segundo": 87.2,
      "fin_segundo": 102.5,
      "duracion_segundos": 15.3,
      "confianza_maxima": 0.88,
      "numero_personas": 3,
      "frames_rango": [872, 1025],
      "imagen_evento": "media/videos/results/event_002_DISTURBIO.jpg",
      "metadata": {}
    }
  ],
  "analysis_report": {
    "total_detections": 15,
    "detections_by_type": {
      "PELEAR": 8,
      "DISTURBIO": 5,
      "NEUTRAL": 2
    },
    "average_confidence": 0.89,
    "critical_events": 13,
    "timeline": [
      {"segundo": 12.5, "evento": "PELEAR", "confianza": 0.95},
      {"segundo": 87.2, "evento": "DISTURBIO", "confianza": 0.88}
    ]
  },
  "created_at": "2026-05-03T14:30:45Z",
  "updated_at": "2026-05-03T15:00:15Z"
}

Response 202 (Aún procesando):
{
  "id": 456,
  "status": "processing",
  "progress_percent": 65,
  "message": "Procesamiento en curso. Intenta de nuevo en 10 segundos."
}

Response 404:
{
  "error": "Video not found",
  "message": "El video con ID {video_id} no existe."
}
```

---

#### **2.2.5 Descargar Video Procesado**
```
GET /api/analysis/videos/{video_id}/download/

Query Params:
  - format: "mp4|webm" (default: mp4)

Response 200:
Content-Disposition: attachment; filename="video_processed_20260503.mp4"
Content-Type: video/mp4

[binary video data]

Response 404:
{
  "error": "Video not found",
  "message": "El video procesado no está disponible."
}
```

---

### 2.3 GENERACIÓN DE FRAMES DESDE VIDEO

#### **2.3.1 Generar Imágenes desde Video**
```
POST /api/analysis/frames/generate-from-video/

Content-Type: multipart/form-data
Body:
  - video: (binary file)
  - fps_value: (int, obligatorio - 1 a 30)
  - max_duration_seconds: (int, optional, default: 30)

Response 200:
{
  "video_filename": "source_video.mp4",
  "fps_extracted": 5,
  "total_frames_generated": 150,
  "duration_seconds": 30,
  "frames": [
    {
      "frame_index": 0,
      "timestamp_sec": 0.0,
      "filename": "frame_0.jpg",
      "base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
      "size_bytes": 45234
    },
    {
      "frame_index": 1,
      "timestamp_sec": 0.2,
      "filename": "frame_1.jpg",
      "base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
      "size_bytes": 46120
    }
  ],
  "processing_time_ms": 2500,
  "message": "Frames generados exitosamente. Total: 150 imágenes."
}

Response 400:
{
  "error": "Invalid parameters",
  "message": "fps_value debe estar entre 1 y 30."
}

Response 413:
{
  "error": "Video too large",
  "message": "Video excede duración máxima de 30 segundos."
}
```

---

## 3. MODELOS DJANGO (YA CREADOS - FASE 2)

Los siguientes modelos ya están definidos en `backend/apps/analysis/models.py`:

```python
class VideoUpload(models.Model):
    """Metadatos del video subido"""
    id_empresa = IntegerField()
    nombre_original = CharField(max_length=255)
    ruta_archivo = CharField(max_length=1024)
    tamaño_bytes = BigIntegerField()
    duracion_segundos = FloatField()
    estado = CharField(max_length=20)  # uploaded, processing, completed, failed
    celery_task_id = CharField(max_length=255, null=True)
    usuario_creacion = IntegerField()
    fecha_creacion = DateTimeField(auto_now_add=True)

class DetectionEvent(models.Model):
    """Evento detectado dentro de un video"""
    video = ForeignKey(VideoUpload, on_delete=CASCADE)
    tipo_evento = CharField(max_length=50)  # PELEAR, DISTURBIO, etc
    confianza = FloatField()
    frame_inicio = IntegerField()
    frame_fin = IntegerField()
    segundo_inicio = FloatField()
    segundo_fin = FloatField()
    detalles_json = JSONField()
    fecha_creacion = DateTimeField(auto_now_add=True)

class PersonKeypoints(models.Model):
    """Keypoints (17 puntos) detectados por persona y frame"""
    detection_event = ForeignKey(DetectionEvent, on_delete=CASCADE)
    person_id = IntegerField()
    frame_index = IntegerField()
    keypoints_json = JSONField()  # Array de 17 keypoints COCO
    fecha_creacion = DateTimeField(auto_now_add=True)

class AnalysisReport(models.Model):
    """Reporte consolidado de análisis de video"""
    video = ForeignKey(VideoUpload, on_delete=CASCADE)
    total_detections = IntegerField()
    detections_by_type = JSONField()
    processing_time_seconds = FloatField()
    resumen_json = JSONField()
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_actualizacion = DateTimeField(auto_now=True)
```

---

## 4. SERIALIZERS A CREAR

```python
# backend/apps/analysis/serializers.py

class KeypointSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    x = serializers.FloatField()
    y = serializers.FloatField()
    z = serializers.FloatField(default=0)
    confidence = serializers.FloatField()

class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    width = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)

class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoUpload
        fields = ['id', 'nombre_original', 'ruta_archivo', 'tamaño_bytes', 
                  'duracion_segundos', 'estado', 'fecha_creacion']

class DetectionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionEvent
        fields = ['id', 'video', 'tipo_evento', 'confianza', 'frame_inicio',
                  'frame_fin', 'segundo_inicio', 'segundo_fin', 'detalles_json']

class AnalysisReportSerializer(serializers.ModelSerializer):
    detections = DetectionEventSerializer(source='detectionevent_set', many=True)
    class Meta:
        model = AnalysisReport
        fields = ['id', 'video', 'total_detections', 'detections_by_type',
                  'processing_time_seconds', 'resumen_json', 'detections']
```

---

## 5. SERVICIOS IA A INTEGRAR (YA DISPONIBLES - FASE 1)

- **`backend/services/pose_detection.py`** - Wrapper de PoseModule (YOLO)
- **`backend/services/behavior_detection.py`** - Wrapper de BehaviorDetector (LSTM)
- **`backend/services/behavior_3d_detection.py`** - BehaviorDetector3D
- **`backend/services/video_processor.py`** - Procesamiento de videos

---

## 6. PLAN DE IMPLEMENTACIÓN (FASE 3)

### Iteración 1: Estructura Base (1-2 días)
- [ ] Crear `backend/apps/analysis/serializers.py` con todos los serializers
- [ ] Crear `backend/apps/analysis/views.py` con ViewSets base
- [ ] Crear `backend/apps/analysis/urls.py` con routers
- [ ] Integrar servicios IA en views

### Iteración 2: Procesamiento de Imágenes (2-3 días)
- [ ] Implementar endpoint POST `/api/analysis/images/upload/`
- [ ] Implementar endpoint POST `/api/analysis/images/resize/`
- [ ] Implementar endpoint POST `/api/analysis/images/save/`
- [ ] Validar con imágenes de prueba

### Iteración 3: Procesamiento de Videos (3-4 días)
- [ ] Implementar endpoint POST `/api/analysis/videos/upload/`
- [ ] Implementar endpoint POST `/api/analysis/videos/{id}/process/` (inicia Celery)
- [ ] Implementar endpoint GET `/api/analysis/videos/{id}/stream/` (SSE)
- [ ] Implementar endpoint GET `/api/analysis/videos/{id}/results/`
- [ ] Validar con videos de prueba

### Iteración 4: Frames y Refinamiento (2-3 días)
- [ ] Implementar endpoint POST `/api/analysis/frames/generate-from-video/`
- [ ] Pruebas de carga y rendimiento
- [ ] Documentación de API (OpenAPI/Swagger)
- [ ] Validación de casos de error

---

## 7. CRITERIOS DE ÉXITO (FASE 3)

- ✅ Puedo subir una imagen y recibir 17 keypoints YOLO
- ✅ Puedo subir un video y procesarlo con LSTM (detección de comportamiento)
- ✅ Stream SSE muestra progreso en tiempo real
- ✅ Resultados se persisten en BD (DetectionEvent, AnalysisReport)
- ✅ Puedo descargar video procesado
- ✅ Puedo generar frames desde video
- ✅ Todos los endpoints responden con formato JSON consistente
- ✅ Errores manejados correctamente (400, 404, 500)
- ✅ Validación de parámetros en todos los endpoints

---

## 8. NOTAS IMPORTANTES

1. **Sin Entrenamiento**: El legacy NO expone endpoint de entrenamiento. Los modelos (YOLO, LSTM) son pre-entrenados y se cargan desde archivos.

2. **Límites de Archivo**: Mantener MAX_CONTENT_LENGTH = 50MB (heredado del legacy)

3. **Autenticación**: Fase 3 puede usar JWT simple o esperar a Fase 6 (DRF SimpleJWT)

4. **Almacenamiento**: Usar `django.core.files.storage` para persister archivos en `media/`

5. **Async Processing**: Fase 3 puede usar colas simples (archivo) antes de integrar Celery en Fase 4

6. **Streaming SSE**: Implementar con Django StreamingHttpResponse o channels

---

## 9. REFERENCIAS

- **Endpoints Legacy**: `Tesis/src/main.py`
- **Servicios IA**: `backend/services/`
- **Modelos BD**: `backend/apps/analysis/models.py`
- **PLAN_MIGRACION_INCREMENTALV2.md**: Líneas 99-138 (especificación de Fase 3)

---

**Próxima Fase**: Fase 4 - Integración de Celery + Redis para tareas distribuidas
