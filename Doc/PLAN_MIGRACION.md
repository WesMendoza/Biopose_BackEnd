# Plan de Migración de Arquitectura del Sistema

## Introducción

Este documento define la estrategia para migrar gradualmente componentes del sistema Flask monolítico actual (ubicado en `Tesis/`) hacia la nueva arquitectura Django distribuida.

El objetivo es separar responsabilidades, facilitar el mantenimiento, mejorar la escalabilidad y permitir que los procesos de detección y análisis puedan ejecutarse de forma desacoplada. La migración NO será de una sola vez, sino en **fases independientes y validables**, minimizando riesgos y permitiendo rollback si es necesario.

## Estado Documental Actual

La documentación activa del proyecto se mantiene en:

- `ESTADO_DOCUMENTACION.md`
- `PLAN_MIGRACION.md` (Este documento)
- `FASE_3_ESPECIFICACION.md`
- `FASE_3_COMPARATIVA_LEGACY_VS_DJANGO.md`
- `FASE_3_QUICK_START.md`
- `Glosario_Desarrollo.md`

Los documentos obsoletos se trasladan a `Doc/archived/` para evitar mezclar referencias antiguas con el estado vigente.

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
- Backend Django puro sin lógica de UI (actuará como centro único de lógica de negocio)
- Separación clara: API, Servicios, Datos, IA
- Apps modulares:
  - `apps.users` - Gestión de usuarios, roles, permisos
  - `apps.analysis` - Detección de pose, comportamiento, análisis
  - `core` - Configuración centralizada
  - `services` - Lógica de integración reutilizable

### Arquitectura Objetivo
- **Django**: autenticación, permisos, menús, configuración, CRUD y panel administrativo.
- **Django REST Framework**: endpoints para frontend y servicios externos.
- **Django Channels**: WebSocket para progreso, alertas y resultados en tiempo real.
- **Celery + Redis**: tareas distribuidas de detección y procesamiento pesado.
- **PostgreSQL**: base de datos principal.
- **Servicio IA separado**: inferencia de pose y comportamiento como módulos independientes del hilo principal web.
- **Frontend actual**: cliente web consumiendo API y WebSocket (o a reemplazar por completo según la estrategia final).

## Fases de Migración

### **Fase 1: Preparación de Servicios de IA (Semana 1)**

**Objetivo**: Crear una capa de servicios que encapsule la lógica de detección sin depender de Flask.

**Estado**: ✅ Completada

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

**Cierre de fase**: ver [backend/FASE_1_COMPLETADA.md](../backend/FASE_1_COMPLETADA.md)

---

### **Fase 2: Crear Modelos Django para Análisis (Semana 1-2)**

**Objetivo**: Definir entidades de BD para almacenar análisis, detecciones y eventos.

**Estado**: ✅ Completada

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

**Cierre de fase**: ver [backend/FASE_2_COMPLETADA.md](../backend/FASE_2_COMPLETADA.md)

---

### **Fase 3: Endpoints REST Básicos (Semana 2)**

**Objetivo**: Exponer servicios de detección a través de API REST y cubrir los flujos legacy de carga/procesamiento de imágenes y videos.

**Estado**: ⏳ Análisis Completado - Implementación en Progreso

**Nota de alcance**: la Iteración 1 dejó la base documental y la estructura de API; la integración real de IA, persistencia y pruebas sigue pendiente.

**Análisis Realizado**:
1. ✅ Identificadas 37 endpoints Flask legacy con métodos, parámetros y respuestas exactas
2. ✅ Especificación detallada de endpoints Django REST en [FASE_3_ESPECIFICACION.md](FASE_3_ESPECIFICACION.md)
3. ✅ Comparativa legacy vs Django en [FASE_3_COMPARATIVA_LEGACY_VS_DJANGO.md](FASE_3_COMPARATIVA_LEGACY_VS_DJANGO.md)
4. ✅ Guía práctica con templates de código en [FASE_3_QUICK_START.md](FASE_3_QUICK_START.md)

**Tareas Pendientes - Implementación**:

**Iteración 1: Estructura Base**
1. Crear `backend/apps/analysis/serializers.py` con 8+ serializers:
   - `KeypointSerializer` - Punto clave (17 COCO)
   - `ImageUploadSerializer` - Recibir imagen
   - `ImageProcessingResponseSerializer` - Respuesta de YOLO
   - `VideoUploadSerializer` - Metadatos video
   - `VideoProcessingRequestSerializer` - Parámetros de procesamiento
   - `DetectionEventSerializer` - Evento detectado
   - `AnalysisReportSerializer` - Reporte consolidado
   - `GenerateFramesRequestSerializer` - Solicitar extracción de frames

2. Crear `backend/apps/analysis/views.py` con ViewSets:
   - `ImageAnalysisViewSet` - Imágenes (upload, resize, save)
   - `VideoAnalysisViewSet` - Videos (upload, process, stream, results, download)
   - `FrameGenerationViewSet` - Frames (generate-from-video)

3. Actualizar `backend/apps/analysis/urls.py` con routers para ViewSets

4. Actualizar `backend/core/urls.py`:
   ```python
   path('api/analysis/', include('apps.analysis.urls')),
   ```

**Iteración 2: Integración IA**
1. Implementar `detect_pose_yolo()` que retorne 17 keypoints COCO
2. Implementar `detect_behavior_lstm()` que retorne DetectionEvents
3. Crear wrapper para BehaviorDetector3D
4. Integrar en views mediante servicios IA

**Iteración 3: Streaming y Persistencia**
1. Implementar SSE (Server-Sent Events) para `/stream/`
2. Persistir resultados en BD (VideoUpload, DetectionEvent, PersonKeypoints)
3. Crear AnalysisReport automáticamente

**Endpoints Fase 3 (9 consolidados de 37 legacy)**:

**Grupo 1: Análisis de Imágenes**
- `POST /api/analysis/images/upload/` - Procesa con YOLO, retorna 17 keypoints
- `POST /api/analysis/images/resize/` - Redimensiona imagen
- `POST /api/analysis/images/save/` - Guarda imagen + keypoints

**Grupo 2: Análisis de Videos**
- `POST /api/analysis/videos/upload/` - Subir video
- `POST /api/analysis/videos/{id}/process/` - Inicia LSTM (retorna 202)
- `GET /api/analysis/videos/{id}/stream/` - SSE: progreso + eventos
- `GET /api/analysis/videos/{id}/results/` - Detecciones consolidadas
- `GET /api/analysis/videos/{id}/download/` - Descargar video procesado

**Grupo 3: Generación de Frames**
- `POST /api/analysis/frames/generate-from-video/` - Extrae frames por FPS

**Mejoras Arquitectónicas**:
- ✅ RESTful semantics (GET para lectura, POST para crear)
- ✅ IDs integer en lugar de filenames
- ✅ HTTP 202 para procesamiento asíncrono explícito
- ✅ SSE estándar para streaming
- ✅ Consolidación de endpoints: -60% complejidad
- ✅ JSON responses uniforme
- ✅ **Documentación Interactiva Automática**: Integración de Swagger UI en `/api/docs/` usando `drf-spectacular` (OpenAPI 3.0)

**Estructura de Almacenamiento**:
```
backend/media/
├── images/
│   ├── uploads/       # Imágenes subidas sin procesar
│   └── processed/     # Imágenes con YOLO + keypoints
└── videos/
    ├── uploads/       # Videos sin procesar
    ├── processing/    # Videos en procesamiento LSTM
    └── results/       # Videos procesados + detectados
```

**Modelos IA Integrados**:
- **YOLO v8s-pose**: 17 keypoints COCO format
  - Input: Imagen JPG/PNG
  - Output: Posición (horizontal/vertical/cuadrada), 17 keypoints con (x, y, z, confidence)
- **LSTM 3-clases**: DISTURBIO, NEUTRAL, PELEAR
  - WINDOW_SIZE: 32 frames
  - Thresholds: TH_PELEAR=0.75, TH_DISTURBIO=0.92
  - Output: DetectionEvent con tipo, confianza, frames, timestamps
- **BehaviorDetector3D**: Versión 3D (opcional en query param dimension=3D)

**Criterio de Éxito**:
- ✅ POST imagen JPG → respuesta JSON con 17 keypoints COCO + posición
- ✅ POST video MP4 → crea VideoUpload, retorna ID
- ✅ POST procesar → HTTP 202, inicia LSTM
- ✅ GET stream → eventos SSE de progreso + detecciones + frames base64
- ✅ GET results → array DetectionEvent consolidados
- ✅ Estructura JSON uniforme en todas respuestas
- ✅ Validación parámetros (400), recurso no existe (404), error servidor (500)
- ✅ Persistencia en BD: VideoUpload, DetectionEvent, PersonKeypoints, AnalysisReport

**Nota Importante**:
- Legacy NO tiene endpoint de entrenamiento; solo INFERENCIA
- Modelos pre-entrenados: YOLO y LSTM cargados desde `backend/resources/models/`
- Fase 3 cubre: carga, procesamiento, inferencia, persistencia (NO reentrenamiento)

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

### **Fase 6: Migración de Autenticación, Usuarios y Multi-tenant (Semana 4)**

**Objetivo**: Migrar sistema de login/permisos del Flask al Django, estableciendo arquitectura multi-tenant (Empresas/Roles dinámicos) y asignaciones estrictas de opciones de menú.

**Estado**: ✅ Completada

**Tareas Completadas**:
1. Creación de la app `apps.authentication`:
   - Endpoint de login: `POST /api/auth/login/` (Valida usuario y retorna JWT)
   - Endpoint de registro: `POST /api/auth/registerAccount/` (Crea usuario con contraseña encriptada)
   - Endpoints de validación: `POST /api/auth/verifyEmail/` y `POST /api/auth/verifyCedula/`
   - Implementación de `CustomJWTAuthentication` y utilidades de hashing y JWT nativo.
2. Refactorización Integral (`apps.users`, `apps.gestionEmpresas`, `apps.menuOpciones`):
   - Mantenimiento estricto del CRUD RESTful con Notación Estándar.
   - Restricciones de permisos: Administradores globales vs Administradores de empresa.
   - Borrado lógico transversal (`estado='I'` o `estado='N'`) implementado.
3. Protección global de endpoints usando el decorador de permisos `IsAuthenticated` (drf).

**Criterios de éxito alcanzados**:
- Login devuelve token JWT válido.
- Endpoints de infraestructura protegidos y con lógica multi-empresa probada y operativa.
- Roles de usuario ahora dependen de las asignaciones de cada empresa y menús correctamente restringidos.

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

Este flujo aplica para cualquier fase futura que modifique tablas, índices, triggers o datos base.

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