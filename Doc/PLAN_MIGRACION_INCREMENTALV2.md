# Plan de Migración Incremental del Sistema

## Introducción

Este documento define la estrategia para migrar gradualmente componentes del sistema Flask monolítico actual (ubicado en `Tesis/`) hacia la nueva arquitectura Django distribuida.

La migración NO será de una sola vez, sino en **fases independientes y validables**, minimizando riesgos y permitiendo rollback si es necesario.

## Estructura Actual vs Nueva

### Sistema Actual (Tesis/src/)
- Monolito Flask con ~2000+ líneas
- Mezcla de lógica de negocio, IA, BD y presentación
- Módulos principales:
  - `main.py` - Controlador principal Flask
  - `Resources/` - Conexión, encriptación, middleware
  - `model/` - PoseDetector, BehaviorDetector (LSTM), BehaviorDetector3d
  - `models/` - Pesos entrenados (LSTM .pt)
  - `static/` - Frontend HTML/JS/CSS
  - `templates/` - Vistas HTML

### Sistema Nuevo (backend/)
- Backend Django puro sin lógica de UI
- Separación clara: API, Servicios, Datos, IA
- Apps modulares:
  - `apps.users` - Gestión de usuarios, roles, permisos
  - `apps.analysis` - Detección de pose, comportamiento, análisis
  - `core` - Configuración centralizada
  - `services` - Lógica de integración reutilizable

## Fases de Migración

### **Fase 1: Preparación de Servicios de IA (Semana 1)**

**Objetivo**: Crear una capa de servicios que encapsule la lógica de detección sin depender de Flask.

**Tareas**:
1. Crear módulo `services/pose_detection.py` que importe `PoseModule.py` del Tesis
2. Crear módulo `services/behavior_detection.py` que importe `BehaviorDetector.py`
3. Crear módulo `services/behavior_3d_detection.py` que importe `BehaviorDetector3d.py`
4. Crear utilidades de procesamiento de video en `services/video_processor.py`
5. Implementar caché local para modelos (YOLO, LSTM)
6. Validar que los servicios funcionen independientemente de Flask/Django

**Archivos a crear**:
- `backend/services/pose_detection.py`
- `backend/services/behavior_detection.py`
- `backend/services/video_processor.py`
- `backend/services/config_loader.py` (para parámetros del sistema)

**Criterio de éxito**:
- Los servicios pueden ejecutarse sin dependencias de Flask
- Se puede importar e instanciar `PoseModule` y ejecutar inferencia en una imagen/video

---

### **Fase 2: Crear Modelos Django para Análisis (Semana 1-2)**

**Objetivo**: Definir entidades de BD para almacenar análisis, detecciones y eventos.

**Tareas**:
1. Crear modelos Django en `backend/apps/analysis/models.py` para:
   - `VideoUpload` - Información del video subido
   - `DetectionEvent` - Evento de comportamiento detectado (pelea, disturbio, etc.)
   - `PersonKeypoints` - Puntos clave detectados de una persona
   - `AnalysisReport` - Reporte consolidado de un análisis
2. Crear script SQL versionado en `scripts/db/update/` (e.g., `001_fase2_analysis_tables.sql`) con:
   - DDL de tablas analysis_* con campos de auditoría e idEmpresa
   - Índices para consultas frecuentes
   - Triggers para auditoría (e.g., actualizar timestamps)
3. **VALIDACIÓN MANUAL**: Revisar script SQL antes de ejecutar
4. **EJECUCIÓN MANUAL**: Ejecutar script en PostgreSQL (psql o herramienta BD) en entorno Dev
5. **ACTUALIZAR SCHEMA**: Modificar `scripts/db/create/Esquema BD.sql` para reflejar nuevas tablas
6. Documentar en `FASE_2_COMPLETADA.md` qué se ejecutó y resultado

**Archivos a crear/modificar**:
- `backend/apps/analysis/models.py` (modelos con `managed=False`)
- `backend/scripts/db/update/001_fase2_analysis_tables.sql` (DDL)
- `backend/scripts/db/create/Esquema BD.sql` (actualizar schema after script execution)
- `Doc/FASE_2_COMPLETADA.md` (nuevo, registrar ejecución manual)

**Criterio de éxito**:
- Modelos Django definidos sin errores (`python manage.py check` pasa)
- Script SQL versionado, validado y documentado
- Script ejecutado manualmente en BD Dev
- Tablas creadas y visibles en PostgreSQL
- Esquema BD.sql actualizado reflejando nuevas tablas
- Se pueden crear registros de análisis en Django shell

---

### **Fase 3: Endpoints REST Básicos (Semana 2)**

**Objetivo**: Exponer servicios de detección a través de API REST.

**Tareas**:
1. Crear serializadores para:
   - Subida de video (`VideoUploadSerializer`)
   - Resultado de análisis (`DetectionEventSerializer`)
2. Crear vistas (ViewSets) para:
   - `/api/analysis/upload-video/` - POST para subir video
   - `/api/analysis/detect-pose/` - POST para detectar pose en imagen
   - `/api/analysis/results/{video_id}/` - GET para obtener resultados
3. Implementar cola básica (archivo) para procesar videos (antes de Celery)

**Archivos a crear**:
- `backend/apps/analysis/serializers.py`
- `backend/apps/analysis/views.py`
- `backend/apps/analysis/urls.py`

**Criterio de éxito**:
- Puedo subir un video desde Postman/cURL a `/api/analysis/upload-video/`
- El backend detecta pose y devuelve JSON con coordenadas de keypoints

---

### **Fase 4: Integración de Celery y Redis (Semana 2-3)**

**Objetivo**: Mover procesamiento pesado a workers asíncronos.

**Tareas**:
1. Configurar Celery en `backend/core/celery.py`
2. Configurar Redis para task broker
3. Crear tareas (`tasks.py`):
   - `process_video_task` - Procesar video completo
   - `detect_pose_single_frame_task` - Detectar pose en un frame
   - `analyze_behavior_task` - Analizar comportamiento
4. Integrar tareas con vistas REST
5. Crear endpoint para consultar estado de tarea (`/api/analysis/task-status/{task_id}/`)

**Archivos a crear**:
- `backend/core/celery.py`
- `backend/apps/analysis/tasks.py`

**Criterio de éxito**:
- Un video de prueba se procesa en background sin bloquear la API
- Puedo consultar el estado de procesamiento en tiempo real

---

### **Fase 5: WebSocket para Tiempo Real (Semana 3-4)**

**Objetivo**: Implementar notificaciones en vivo de análisis.

**Tareas**:
1. Configurar Django Channels
2. Crear Consumer para WebSocket:
   - `AnalysisConsumer` - Notificaciones de detecciones
   - `LiveDetectionConsumer` - Streaming de cámara en vivo
3. Emitir eventos desde tareas Celery cuando detecte comportamientos
4. Cliente JavaScript que consume WebSocket (reutilizar del Tesis con adaptaciones)

**Archivos a crear**:
- `backend/core/asgi.py` (actualizar)
- `backend/apps/analysis/consumers.py`
- `backend/apps/analysis/routing.py`

**Criterio de éxito**:
- Puedo conectarme a WebSocket y recibir notificaciones de análisis en vivo

---

### **Fase 6: Migración de Autenticación (Semana 4)**

**Objetivo**: Migrar sistema de login/permisos del Flask al Django.

**Tareas**:
1. Crear endpoint de login: `/api/users/login/` (POST con email/password)
2. Implementar JWT o Session tokens
3. Crear decorador/permission class para proteger endpoints de IA
4. Validar que usuarios solo accedan a sus propios análisis

**Archivos a modificar**:
- `backend/apps/users/views.py` (agregar LoginViewSet)
- `backend/apps/users/serializers.py`
- `backend/core/settings.py` (configurar JWT si aplica)

**Criterio de éxito**:
- Login devuelve token válido
- Endpoints protegidos rechaza sin token válido

---

### **Fase 7: Frontend Consumidor (Semana 4-5)**

**Objetivo**: Adaptar el frontend para consumir nueva API Django.

**Tareas**:
1. Crear carpeta `frontend/` fuera del backend
2. Adaptar scripts JavaScript para:
   - Consumir endpoints API en lugar de Flask
   - Conectarse a WebSocket de Django Channels
3. Mantener templates HTML actuales como punto de partida
4. Implementar progreso visual de procesamiento

**Archivos**:
- Reutilizar `Tesis/src/static/scripts/` con adaptaciones
- Nueva carpeta `frontend/` con lógica separada

**Criterio de éxito**:
- Frontend original funciona contra nueva API Django
- Puedo subir video y ver análisis en tiempo real

---

## Tareas Inmediatas (Hoy)

Para comenzar ahora mismo:

### 1. Crear estructura de servicios
```
backend/
  ├── services/
  │   ├── __init__.py
  │   ├── pose_detection.py
  │   ├── behavior_detection.py
  │   ├── video_processor.py
  │   └── config_loader.py
  └── ...
```

### 2. Copiar módulos del Tesis
- Copiar `Tesis/src/model/PoseModule.py` → `backend/services/models/PoseModule.py`
- Copiar `Tesis/src/model/BehaviorDetector.py` → `backend/services/models/BehaviorDetector.py`
- Copiar `Tesis/src/model/BehaviorDetector3d.py` → `backend/services/models/BehaviorDetector3d.py`
- Copiar `Tesis/src/Resources/` → `backend/services/resources/`

### 3. Actualizar settings.py
- Agregar `apps.analysis` a `INSTALLED_APPS`
- Configurar ruta de modelos YOLO/LSTM
- Crear variable de entorno `AI_MODELS_PATH`

### 4. Crear archivo de configuración
- `backend/services/config_loader.py` para parámetros del sistema (thresholds, window_size, etc.)

### 5. Proceso de Cambios BD (IMPORTANTE)
**Control Manual**: Todo cambio de BD debe ser versionado, validado y ejecutado manualmente:
  1. Crear script SQL en `scripts/db/update/` (e.g., `001_fase2_analysis_tables.sql`)
  2. Validar sintaxis y dependencias manualmente
  3. Ejecutar script manualmente en PostgreSQL (psql/herramienta BD)
  4. **ACTUALIZAR** `scripts/db/create/Esquema BD.sql` con el nuevo estado del schema
  5. Registrar cambio en archivo de control de fase (FASE_X_COMPLETADA.md)

## Dependencias por Fase

```
Fase 1 (Servicios) → Fase 2 (Modelos) → Fase 3 (API) 
                                      ↓
                                  Fase 4 (Celery)
                                      ↓
                                  Fase 5 (WebSocket)
                                      ↓
                                  Fase 6 (Auth)
                                      ↓
                                  Fase 7 (Frontend)
```

## Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Modelos YOLO/LSTM no cargan | Probar carga en Fase 1, tener ruta clara |
| Pérdida de rendimiento | Benchmarking antes/después, usar caché |
| Incompatibilidad BD | Mantener CreateDb.sql como referencia, usar managed=False |
| Saltos de usuario a nuevo sistema | Mantener Flask operativo durante transición |
| Errores en cambios BD sin validación previa | **Control Manual Obligatorio**: revisar script antes de ejecutar, documentar en Esquema BD.sql |
| Pérdida de trazabilidad de cambios BD | Registrar ejecución en FASE_X_COMPLETADA.md: fecha, script, resultado, cambios al schema |

## Checklist de Validación

- [ ] Sistema Flask original funciona sin cambios
- [ ] Servicios IA pueden importarse e usarse sin Flask
- [ ] Script SQL de Fase 2 creado y validado manualmente
- [ ] Script SQL de Fase 2 ejecutado manualmente en BD Dev
- [ ] Esquema BD.sql actualizado reflejando nuevas tablas de Fase 2
- [ ] Modelos Django migran sin errores
- [ ] Primeros endpoints REST responden correctamente
- [ ] Celery procesa tareas en background
- [ ] WebSocket emite eventos en vivo
- [ ] Autenticación redirige correctamente
- [ ] Frontend consume nueva API
- [ ] Permisos y roles funcionan en nueva API
- [ ] Registros de ejecución documentados en FASE_X_COMPLETADA.md

## Timeline Estimado

- **Semana 1**: Fases 1-2
- **Semana 2**: Fases 3-4
- **Semana 3-4**: Fases 5-6
- **Semana 4-5**: Fase 7 + estabilización

Total: **4-5 semanas** para migración completa.
