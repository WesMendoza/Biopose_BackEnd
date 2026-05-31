# FASE 3: Endpoints REST Básicos - Iteración 1 Completada ✅

**Estado**: ⏳ Estructura Base Implementada - Integración IA, persistencia y pruebas pendientes

**Alcance real de esta iteración**: se creó la base documental y la estructura de ViewSets/serializers/routers, pero todavía no hay una implementación productiva completa de los endpoints.

**Fecha de Inicio**: 2026-05-03
**Fecha de Finalización de Iteración 1**: 2026-05-03

---

## Tareas Completadas - Iteración 1

### 1. Documentación Completa ✅

- [x] **PLAN_MIGRACION_INCREMENTALV2.md** - Fase 3 actualizada con:
  - Análisis completo de 37 endpoints legacy → 9 endpoints Django REST
  - 3 iteraciones de implementación detalladas
  - Estructura de media folder (images/, videos/, frames/)
  - Criterios de éxito y metricas de mejora

- [x] **Glosario_Desarrollo.md** - Nuevos términos Fase 3 agregados:
  - Serializer, ViewSet, RESTful, HTTP 202, SSE
  - YOLO, LSTM, COCO Format, Keypoints
  - Behavior Detection, Confidence, Streaming, File Upload
  - 25+ términos nuevos documentados

- [x] **ESPECIFICACION_DESARROLLO.md** - Estructura media/ actualizada:
  - Recomendación de carpeta backend/media/ como centro de almacenamiento
  - Subdirectorios: images/uploads/, images/processed/, videos/uploads/, videos/processing/, videos/results/
  - Ventajas: centralización, claridad, escalabilidad, seguridad

- [x] **README.md** - Fase 3 actualizado a:
  - Status: "⏳ Análisis Completado - Implementación en Progreso"
  - Endpoints consolidados listados (9 totales)
  - Mejoras arquitectónicas documentadas

### 2. Código Python Fase 3 Creado (Refactorización Modular) ✅

Se implementó la nueva estructura modular dentro de `backend/apps/analysis/api/` en reemplazo del antiguo monolito.

#### **Módulo Media (`api/media/`)**

✅ `serializers.py`: `ImageUploadSerializer`, `VideoUploadSerializer`
✅ `views.py`: `ImageUploadView`, `VideoUploadView`
✅ `urls.py`: Rutas de subida

- `POST /api/analysis/media/images/upload/`
- `POST /api/analysis/media/videos/upload/`

#### **Módulo Pose (`api/pose/`)**

✅ `serializers.py`: `KeypointSerializer`, `PersonPoseSerializer`, etc.
✅ `views.py`: `PoseDetectionImageView` (procesamiento YOLO + guardado de imagen anotada)
✅ `urls.py`: Rutas de detección de keypoints

- `POST /api/analysis/pose/image/`

#### **Módulo Behavior (`api/behavior/`)**

✅ `serializers.py`: `DetectionEventSerializer`, `AnalysisReportSerializer`, `VideoProcessRequestSerializer`
✅ `views.py`: `VideoProcessView`, `VideoResultsView` (inicio de procesamiento LSTM)
✅ `urls.py`: Rutas de procesamiento y obtención de resultados

- `POST /api/analysis/behavior/videos/{video_id}/process/`
- `GET /api/analysis/behavior/videos/{video_id}/results/`

#### **Router Principal (`api/router.py`)**

✅ Archivo `router.py` enruta tráfico hacia `media/`, `pose/` y `behavior/`.

### 3. Arquitectura REST Implementada ✅

**Endpoints Fase 3 (9 consolidados)**:

#### Grupo 1: Análisis de Imágenes (3)

- `POST /api/analysis/media/images/upload/` - YOLO v8s-pose → 17 keypoints COCO
- `POST /api/analysis/images/resize/` - Redimensiona imagen
- `POST /api/analysis/images/save/` - Guarda imagen + keypoints en BD

#### Grupo 2: Análisis de Videos (5)

- `POST /api/analysis/media/videos/upload/` - Subir video (crea VideoUpload)
- `POST /api/analysis/videos/{id}/process/` - HTTP 202: inicia LSTM
- `GET /api/analysis/videos/{id}/stream/` - SSE: progreso + eventos
- `GET /api/analysis/videos/{id}/results/` - Detecciones consolidadas
- `GET /api/analysis/videos/{id}/download/` - Descarga video procesado

#### Grupo 3: Generación de Frames (1)

- `POST /api/analysis/frames/generate-from-video/` - Extrae frames por FPS

---

## Tareas Pendientes - Iteración 2

### Integración de Servicios IA

1. **Importar servicios IA** (Fase 2)
   - [ ] `from services.pose_detection import detect_pose_yolo`
   - [ ] `from services.behavior_detection import detect_behavior_lstm`
   - [ ] Validar que modelos están en `backend/resources/models/`

2. **Implementar ImageAnalysisViewSet.upload()**
   - [ ] Guardar imagen en `backend/media/images/uploads/`
   - [ ] Llamar `detect_pose_yolo(image_path)`
   - [ ] Extraer 17 keypoints en formato COCO
   - [ ] Determinar orientación (horizontal/vertical/cuadrada)
   - [ ] Guardar imagen procesada en `backend/media/images/processed/`
   - [ ] Retornar respuesta JSON con keypoints

3. **Implementar VideoAnalysisViewSet.upload()**
   - [ ] Validar archivo MP4/MOV
   - [ ] Guardar en `backend/media/videos/uploads/`
   - [ ] Extraer metadatos (duración, FPS, resolución)
   - [ ] Crear registro VideoUpload en BD
   - [ ] Retornar ID + metadatos

4. **Implementar VideoAnalysisViewSet.process()**
   - [ ] Validar parámetros (mode, dimension, fps_skip, confidence_threshold)
   - [ ] Crear task Celery (Fase 4) o ejecutar directamente (prototype)
   - [ ] Guardar video temporalmente en `backend/media/videos/processing/`
   - [ ] Procesar frames con LSTM
   - [ ] Crear DetectionEvent por detección
   - [ ] Guardar keypoints en PersonKeypoints
   - [ ] Generar AnalysisReport
   - [ ] Mover resultado a `backend/media/videos/results/`

5. **Implementar VideoAnalysisViewSet.stream()**
   - [ ] Monitorear progreso de procesamiento
   - [ ] Emitir eventos SSE de progreso (cada 5-10 frames)
   - [ ] Emitir eventos SSE de detección (al detectar evento)
   - [ ] Emitir evento SSE de finalización
   - [ ] Incluir base64 de frames si es necesario (modo analitico)

6. **Implementar FrameGenerationViewSet.generate_from_video()**
   - [ ] Guardar video temporalmente
   - [ ] Usar OpenCV para extraer frames
   - [ ] Aplicar fps_value para muestreo
   - [ ] Guardar frames en `backend/media/images/`
   - [ ] Codificar a base64 para respuesta
   - [ ] Retornar lista de frames

---

## Tareas Pendientes - Iteración 3

### Optimización y Testing

1. **Streaming y Persistencia**
   - [ ] Implementar SSE con yield generator
   - [ ] Persistir toda cadena de procesamiento en BD
   - [ ] Índices en PostgreSQL para queries rápidas
   - [ ] Limpieza de archivos temporales

2. **Testing Completo**
   - [ ] Tests unitarios para serializers
   - [ ] Tests de integración para endpoints
   - [ ] Tests de carga (video 100MB+)
   - [ ] Validación de respuestas JSON
   - [ ] Tests de errores (400, 404, 500)

3. **Documentación Swagger/OpenAPI**
   - [ ] Instalar drf-spectacular
   - [ ] Agregar docstrings OpenAPI
   - [ ] Generar UI interactiva en /api/schema/swagger/
   - [ ] Documentar todos los parámetros y respuestas

4. **Production Readiness**
   - [ ] CORS headers configurados
   - [ ] Rate limiting en endpoints
   - [ ] Authentication (JWT si es necesario)
   - [ ] Validación de tamaño máximo de archivos
   - [ ] Compresión de respuestas

---

## Notas Importantes

### Estructura de Media Folder

```
backend/media/
├── images/
│   ├── uploads/       # ← POST /media/images/upload/ guarda aquí
│   └── processed/     # ← YOLO retorna aquí
├── videos/
│   ├── uploads/       # ← POST /media/videos/upload/ guarda aquí
│   ├── processing/    # ← Procesamiento LSTM aquí (temporal)
│   └── results/       # ← Video final procesado aquí
└── reports/
    └── analysis_report_*.json
```

### Modelos IA Integrados

- **YOLO v8s-pose**: 17 keypoints COCO, tiempo ~0.25s por imagen
- **LSTM 3-class**: Clasifica DISTURBIO, NEUTRAL, PELEAR. Window size: 32 frames
  - TH_PELEAR: 0.75
  - TH_DISTURBIO: 0.92
- **BehaviorDetector3D**: Variante 3D (query param dimension=3D)

### HTTP Status Codes

- `200 OK` - Procesamiento exitoso, respuesta lista
- `202 Accepted` - Procesamiento asíncrono aceptado (POST /videos/{id}/process/)
- `400 Bad Request` - Validación fallida (formato archivo, parámetros inválidos)
- `404 Not Found` - Video/imagen no existe
- `500 Internal Server Error` - Error en IA o BD

### Próximos Pasos

1. **Fase 3.2**: Integrar servicios IA y persistencia BD
2. **Fase 4**: Implementar Celery para procesamiento asíncrono escalable
3. **Fase 5**: Frontend React para UI de carga/resultados

---

## Referencias

- [PLAN_MIGRACION_INCREMENTALV2.md](PLAN_MIGRACION_INCREMENTALV2.md) - Plan completo
- [FASE_3_ESPECIFICACION.md](../Doc/FASE_3_ESPECIFICACION.md) - Especificación técnica
- [FASE_3_COMPARATIVA_LEGACY_VS_DJANGO.md](../Doc/FASE_3_COMPARATIVA_LEGACY_VS_DJANGO.md) - Análisis legacy
- [FASE_3_QUICK_START.md](../Doc/FASE_3_QUICK_START.md) - Guía práctica
