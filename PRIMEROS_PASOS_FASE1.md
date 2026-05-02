# Primeros Pasos - Fase 1 de Migración

## ¿Qué se acaba de implementar?

Se ha preparado la estructura base para iniciar la migración gradual del sistema Flask (monolito) hacia el nuevo backend Django distribuido.

### 1. **Plan de Migración Incremental** 
Documento: `Doc/PLAN_MIGRACION_INCREMENTALV2.md`
- Define 7 fases con tareas específicas
- Cada fase es independiente y validable
- Riesgos y mitigaciones documentados
- Timeline realista de 4-5 semanas

### 2. **Nueva App "Analysis"** 
Carpeta: `backend/apps/analysis/`
- **Modelos**: VideoUpload, DetectionEvent, AnalysisReport, SystemParameter
- **Serializadores**: Mapeos JSON para API REST
- **Vistas**: ViewSets para CRUD de videos y eventos
- **URLs**: Enrutamiento de endpoints `/api/analysis/*`

Nuevos endpoints:
- `GET/POST /api/analysis/videos/` - Gestión de videos
- `GET /api/analysis/videos/{id}/eventos/` - Eventos de un video
- `GET /api/analysis/videos/{id}/reporte/` - Reporte consolidado
- `GET /api/analysis/eventos/` - Listar eventos
- `GET/POST /api/analysis/parametros/` - Configuración del sistema

### 3. **Capa de Servicios (Services)**
Carpeta: `backend/services/`

**Archivos creados**:
- `pose_detection.py` - Detección de keypoints con YOLO
  - `PoseDetectionService.detect_pose_image()`
  - `PoseDetectionService.detect_pose_frame()`
  - `PoseDetectionService.detect_pose_with_tracking()`
  
- `behavior_detection.py` - Clasificación de comportamientos con LSTM
  - `BehaviorDetectionService.predict_behavior()`
  - Preprocesamiento de secuencias de keypoints
  
- `config_loader.py` - Configuración centralizada
  - Parámetros de YOLO, LSTM, thresholds
  - Rutas de procesamiento
  - Variables de entorno
  
- `__init__.py` - Factory para instanciar servicios
  - `initialize_services()`
  - `get_pose_service()`
  - `get_behavior_service()`

---

## Próximos Pasos Inmediatos

### Paso 1: Actualizar archivo `.env`
Agrega estas variables a `backend/.env`:

```env
# Modelos IA
YOLO_MODEL_PATH=Tesis/src/yolov8s-pose.pt
YOLO_DEVICE=cpu
LSTM_MODEL_PATH=Tesis/src/models/lstm_3clasesstride1.pt
LABEL_MAP_PATH=Tesis/src/models/label_map_3clases.json

# Thresholds de detección
THRESHOLD_PELEA=0.75
THRESHOLD_DISTURBIO=0.92
MIN_EVENT_PELEA=25
MIN_EVENT_DISTURBIO=60

# Rutas
VIDEOS_UPLOAD_DIR=media/videos/uploads
VIDEOS_RESULTS_DIR=media/videos/results
PROCESSED_VIDEOS_DIR=media/videos/processed
MAX_VIDEO_SIZE_MB=500

# Celery (para siguiente fase)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Paso 2: Probar carga de modelos
Ejecuta este comando en una terminal Python dentro del venv:

```python
cd backend
python
>>> from services import get_pose_service, get_behavior_service
>>> pose_srv = get_pose_service()
>>> behavior_srv = get_behavior_service()
>>> print("✓ Servicios cargados correctamente")
```

### Paso 3: Migrar BD
```powershell
cd backend
python manage.py migrate
```

### Paso 4: Probar endpoints
Con el servidor corriendo:
```bash
curl http://127.0.0.1:8000/api/analysis/videos/
```

Debería retornar una lista vacía: `[]`

---

## Estructura Actual del Proyecto

```
Biopose_BackEnd/
├── Tesis/                      (Sistema anterior Flask - NO MODIFICAR AÚN)
│   └── src/
│       ├── main.py
│       ├── model/
│       ├── models/             (Pesos YOLO, LSTM)
│       └── Resources/
│
├── backend/                    (Nuevo sistema Django)
│   ├── core/
│   │   ├── settings.py         (✓ Actualizado)
│   │   ├── urls.py             (✓ Actualizado)
│   │   └── asgi.py
│   ├── apps/
│   │   ├── users/              (✓ Completado)
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   └── analysis/           (✓ NUEVO)
│   │       ├── models.py
│   │       ├── serializers.py
│   │       ├── views.py
│   │       └── urls.py
│   └── services/               (✓ NUEVO - Capa reutilizable)
│       ├── pose_detection.py
│       ├── behavior_detection.py
│       ├── config_loader.py
│       └── __init__.py
│
└── Doc/
    ├── MIGRACION_ARQUITECTURA.md
    ├── ESPECIFICACION_DESARROLLO.md
    └── PLAN_MIGRACION_INCREMENTALV2.md   (✓ NUEVO)
```

---

## Validación de Fase 1

Checklist para confirmar que todo está listo:

- [ ] `.env` actualizado con rutas de modelos
- [ ] `python manage.py migrate` ejecuta sin errores
- [ ] Servicios se cargan sin excepciones
- [ ] Endpoint `/api/analysis/videos/` responde con `[]`
- [ ] Endpoint `/api/analysis/parametros/` responde correctamente

Una vez hayas confirmado esto, avisame y pasamos a:
- **Fase 2**: Crear migraciones para tabla `videoUpload` y `detectionEvent` en BD
- **Fase 3**: Implementar endpoint de subida y procesamiento de video
