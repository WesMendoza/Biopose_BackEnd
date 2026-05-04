# COMPARATIVA: Legacy Flask vs Nuevo Django - FASE 3

## Mapeo de Endpoints Flask → Endpoints Django REST

### GRUPO 1: PROCESAMIENTO DE IMÁGENES

| Funcionalidad | Endpoint Flask (Legacy) | Método | Endpoint Django (Nuevo) | Método | Cambios | Status |
|---|---|---|---|---|---|---|
| Procesar imagen + YOLO | `/upload` | POST | `/api/analysis/images/upload/` | POST | Response JSON mejorada con keypoints nombrados | ✅ Nuevo |
| Redimensionar imagen | `/resize_image` | POST | `/api/analysis/images/resize/` | POST | Multipart a form data, response estructurada | ✅ Nuevo |
| Redimensionar con params | `/resize_image_params` | POST | `/api/analysis/images/resize/` | POST | Consolidado en endpoint único | ✅ Simplificado |
| Guardar imagen + keypoints | `/save` | POST | `/api/analysis/images/save/` | POST | JSON input mejorado, mejor validación | ✅ Nuevo |
| Procesar imagen de video | `/upload_image_video` | POST | `/api/analysis/images/upload/` | POST | Reutiliza endpoint de upload (source agnostic) | ✅ Consolidado |
| Guardar imagen de video | `/save_image_from_video` | POST | `/api/analysis/images/save/` | POST | Reutiliza endpoint de save | ✅ Consolidado |
| Obtener imagen | `/getImage` | POST | `/api/analysis/images/{id}/download/` | GET | RESTful GET, mejor identificación | ✅ Mejorado |

**Mejora Principal**: Se **consolidan múltiples endpoints** en versiones únicas más genéricas.

---

### GRUPO 2: PROCESAMIENTO DE VIDEOS - FLUJO LSTM

| Funcionalidad | Endpoint Flask (Legacy) | Método | Endpoint Django (Nuevo) | Método | Cambios | Status |
|---|---|---|---|---|---|---|
| Subir video | `/save-video-lstm` | POST | `/api/analysis/videos/upload/` | POST | Respuesta con metadata (duración, tamaño) | ✅ Nuevo |
| Iniciar procesamiento | `/process-video` | POST | `/api/analysis/videos/{id}/process/` | POST | POST a recurso específico (RESTful), retorna 202 | ✅ Mejorado |
| Stream progreso+eventos | `/stream_frames_lstm/<filename>/<mode>/<dimension>` | GET | `/api/analysis/videos/{id}/stream/` | GET | Params en query string en lugar de path, SSE estándar | ✅ Mejorado |
| Obtener resultados | `/results-video-lstm/<filename>` | GET | `/api/analysis/videos/{id}/results/` | GET | Response consolidada con análisis completo | ✅ Mejorado |
| Descargar video procesado | `/processed-video-lstm/<filename>` | GET | `/api/analysis/videos/{id}/download/` | GET | Format param para elegir tipo de archivo | ✅ Mejorado |
| Listar detecciones LSTM | `/detecciones-lstm` | GET | `/api/analysis/detections/` | GET | Endpoint nuevo para listar todas las detecciones | ✅ Nuevo |

**Mejora Principal**: Endpoints **RESTful con IDs** en lugar de filenames, mejor HTTP semantics.

---

### GRUPO 3: DETECCIÓN 2D/3D EN VIVO Y VIDEO

| Funcionalidad | Endpoint Flask (Legacy) | Método | Endpoint Django (Nuevo) | Método | Cambios | Status |
|---|---|---|---|---|---|---|
| Stream frames 2D/3D | `/stream_frames/<filename>/<frame_skip>/<dimension>` | GET | `/api/analysis/videos/{id}/stream/?dimension=2D/3D` | GET | Query params en lugar de path, SSE estándar | ✅ Mejorado |
| Stream cámara | `/camera_stream_frames/<frame_skip>/<dimension>/<connection>` | GET | `/api/analysis/live/camera-stream/?dimension=2D/3D` | GET | Ruta mejorada, conexión en query string | 📋 Fase 5 |
| Transmisión en vivo | `/live-actions` | GET | `/api/analysis/live/actions/` | GET | Simplificado, compatible con WebSocket | 📋 Fase 5 |
| Transmisión remota | `/live-actions-remote/<stream_url>/<mode>` | GET | `/api/analysis/live/remote/?stream_url=...&mode=...` | GET | Query params estructurados | 📋 Fase 5 |
| Evaluación final video | `/evaluate-final/<filename>/<mode>` | GET | `/api/analysis/videos/{id}/evaluate/?mode=...` | GET | RESTful con ID + query param | 📋 Fase 4 |
| Video procesado | `/processed-video/<filename>` | GET | `/api/analysis/videos/{id}/download/` | GET | Consolidado | ✅ Consolidado |

**Notas**: 
- Endpoints en vivo (live) se abordan en **Fase 5 (WebSocket)**
- Evaluación se integra con procesamiento en **Fase 4**

---

### GRUPO 4: GENERACIÓN DE FRAMES

| Funcionalidad | Endpoint Flask (Legacy) | Método | Endpoint Django (Nuevo) | Método | Cambios | Status |
|---|---|---|---|---|---|---|
| Generar imágenes desde video | `/generate_images_from_videos` | POST | `/api/analysis/frames/generate-from-video/` | POST | Nombre descriptivo, response con array de frames base64 | ✅ Nuevo |

---

### GRUPO 5: AUTENTICACIÓN Y USUARIOS

| Funcionalidad | Endpoint Flask (Legacy) | Método | Endpoint Django (Nuevo) | Método | Cambios | Status |
|---|---|---|---|---|---|---|
| Login | `/validateLogin` | POST | `/api/users/login/` | POST | RESTful path, DRF + SimpleJWT | 📋 Fase 6 |
| Crear cuenta | `/createAccount` | POST | `/api/users/register/` | POST | Renombrado, validación mejorada | 📋 Fase 6 |
| Listar usuarios | `/users-all` | GET | `/api/users/` | GET | RESTful GET, paginación | 📋 Fase 6 |
| Obtener usuario | `/user-one` | POST | `/api/users/{id}/` | GET | RESTful GET con ID, no POST | 📋 Fase 6 |
| Verificar email | `/check_email` | POST | `/api/users/check-email/` | POST | Action endpoint | 📋 Fase 6 |
| Verificar cédula | `/check_cedula` | POST | `/api/users/check-cedula/` | POST | Action endpoint | 📋 Fase 6 |
| Eliminar usuario | `/delete_user` | POST | `/api/users/{id}/` | DELETE | RESTful DELETE | 📋 Fase 6 |
| Editar usuario | `/edit_user` | POST | `/api/users/{id}/` | PUT/PATCH | RESTful PUT/PATCH | 📋 Fase 6 |

**Notas**: Todos los endpoints de autenticación/usuarios se implementan en **Fase 6**.

---

### GRUPO 6: GESTIÓN DE RUTAS Y CARPETAS

| Funcionalidad | Endpoint Flask (Legacy) | Método | Endpoint Django (Nuevo) | Método | Cambios | Status |
|---|---|---|---|---|---|---|
| Guardar ruta principal | `/parametrizador-ruta-principal` | POST | `/api/users/{id}/settings/primary-path/` | POST | Anidado bajo usuario | 📋 Fase 6 |
| Validar ruta existe | `/validate_has_path` | POST | `/api/users/{id}/settings/primary-path/validate/` | GET | RESTful GET | 📋 Fase 6 |
| Obtener ID ruta | `/getIdMainPath` | POST | `/api/users/{id}/settings/primary-path-id/` | GET | Información en response | 📋 Fase 6 |
| Crear carpeta | `/save_new_folder` | POST | `/api/users/{id}/folders/` | POST | Anidado bajo usuario | 📋 Fase 6 |
| Listar rutas | `/all_paths` | POST | `/api/users/{id}/paths/` | GET | RESTful GET | 📋 Fase 6 |
| Eliminar carpeta | `/delete_folder` | POST | `/api/users/{id}/folders/{folder_id}/` | DELETE | RESTful DELETE | 📋 Fase 6 |
| Archivos por ruta | `/getFilesByPathname` | POST | `/api/files/?path=...` | GET | Query param estructurado | 📋 Fase 6 |
| Obtener archivos | `/getFiles` | POST | `/api/files/{id}/` | GET | RESTful GET | 📋 Fase 6 |

**Notas**: Gestión de rutas anidada bajo `/api/users/`. Se implementa en **Fase 6**.

---

### GRUPO 7: PARAMETRIZACIÓN FPS

| Funcionalidad | Endpoint Flask (Legacy) | Método | Endpoint Django (Nuevo) | Método | Cambios | Status |
|---|---|---|---|---|---|---|
| Guardar FPS | `/saveNewFrame` | POST | `/api/users/{id}/settings/fps/` | POST | Anidado bajo usuario | 📋 Fase 6 |
| Obtener FPS | `/get_frames` | POST | `/api/users/{id}/settings/fps/` | GET | RESTful GET | 📋 Fase 6 |

---

## RESUMEN DE CAMBIOS ARQUITECTÓNICOS

### Cambios Positivos (Fase 3)

| Aspecto | Legacy Flask | Nuevo Django | Beneficio |
|---|---|---|---|
| **Convención de rutas** | Mezcladas (POST para GET, filenames en path) | RESTful (GET/POST/PUT/DELETE, IDs en path) | Consistencia, estándar HTTP |
| **Consolidación endpoints** | Múltiples endpoints para casos similares | Endpoints genéricos y reutilizables | Menos código, mantenimiento simplificado |
| **Manejo de parámetros** | Query string + path + form data mezclados | Convenciones claras por tipo de endpoint | Menos confusión, API más predecible |
| **Respuestas** | Formatos inconsistentes (a veces `success`, a veces `result`) | Estructura JSON uniforme con metadatos | Clientes más simples, documentación clara |
| **Identificación de recursos** | Filenames (string) | ID (integer) | Mejor trazabilidad en BD, más seguro |
| **Stream de progreso** | `/stream_frames_lstm/<>` con modes en path | `/stream/?mode=...` con SSE estándar | Mejor separación concerns, compatible con clientes HTTP |
| **Async processing** | Bloqueante o callback implícito | Celery + HTTP 202 explícito | Escalabilidad clara, mejor UX |

---

## ENDPOINTS FASE 3 - RESUMEN RÁPIDO

### ✅ **Fase 3 (Nuevo - REST + Servicios IA)**

```
ANÁLISIS DE IMÁGENES:
  POST   /api/analysis/images/upload/           # Procesar imagen con YOLO
  POST   /api/analysis/images/resize/           # Redimensionar
  POST   /api/analysis/images/save/             # Guardar con keypoints

ANÁLISIS DE VIDEOS:
  POST   /api/analysis/videos/upload/           # Subir video
  POST   /api/analysis/videos/{id}/process/     # Iniciar procesamiento LSTM
  GET    /api/analysis/videos/{id}/stream/      # SSE: progreso + eventos
  GET    /api/analysis/videos/{id}/results/     # Obtener detecciones consolidadas
  GET    /api/analysis/videos/{id}/download/    # Descargar video procesado

GENERACIÓN DE FRAMES:
  POST   /api/analysis/frames/generate-from-video/  # Extrae frames por FPS
```

---

### 📋 **Fase 6 (Usuarios, Autenticación)**

```
USUARIOS Y AUTENTICACIÓN:
  POST   /api/users/login/                      # Login con JWT
  POST   /api/users/register/                   # Crear cuenta
  GET    /api/users/                            # Listar usuarios
  GET    /api/users/{id}/                       # Detalle usuario
  PUT    /api/users/{id}/                       # Actualizar usuario
  DELETE /api/users/{id}/                       # Eliminar usuario
  
CONFIGURACIÓN POR USUARIO:
  GET    /api/users/{id}/settings/primary-path/
  POST   /api/users/{id}/settings/primary-path/
  GET    /api/users/{id}/settings/fps/
  POST   /api/users/{id}/settings/fps/
  
GESTIÓN DE RUTAS:
  GET    /api/users/{id}/paths/                 # Listar rutas
  POST   /api/users/{id}/folders/               # Crear carpeta
  DELETE /api/users/{id}/folders/{folder_id}/   # Eliminar carpeta
```

---

### 📋 **Fase 5 (WebSocket - Tiempo Real)**

```
EN VIVO (WebSocket):
  WS     /ws/live/camera-stream/                # Cámara en vivo 2D/3D
  WS     /ws/live/actions/                      # Detección en vivo
  WS     /ws/live/remote/                       # Stream remoto
```

---

### 📋 **Fase 4 (Celery - Tareas Distribuidas)**

```
ESTADO DE TAREAS:
  GET    /api/analysis/tasks/{task_id}/status/  # Consultar estado
```

---

## NOTAS IMPORTANTES

1. **Consolidación**: Se reducen de 37 endpoints legacy a ~15 endpoints principales en Fase 3.
2. **RESTful Compliance**: Todos los nuevos endpoints siguen convenciones REST.
3. **Backward Compatibility**: NO hay compatibilidad backward. El legacy seguirá funcionando independientemente durante la transición.
4. **Fases Dependientes**: 
   - Fase 3 no depende de Fase 4-6
   - Fase 4 (Celery) mejora Fase 3 pero no es requerida
   - Fase 5 (WebSocket) es opcional para casos en vivo
   - Fase 6 es independiente (autenticación)
5. **Modelos IA**: 
   - YOLO (pose): Integrado en Fase 3
   - LSTM (comportamiento): Integrado en Fase 3 (sincróno), mejorado con Celery en Fase 4

---

## CRITERIOS DE ACEPTACIÓN

Para validar que Fase 3 está completa:

- ✅ Puedo subir una imagen JPG/PNG y recibir 17 keypoints YOLO
- ✅ Puedo redimensionar imágenes
- ✅ Puedo guardar imagen + keypoints en BD
- ✅ Puedo subir un video MP4/MOV
- ✅ Puedo procesar video con LSTM y recibir 202 (aceptado)
- ✅ Puedo conectarme a `/stream/` y recibir SSE con progreso
- ✅ Puedo consultar `/results/` y obtener DetectionEvents consolidados
- ✅ Puedo descargar video procesado
- ✅ Puedo generar frames desde video en base64
- ✅ Todos los endpoints retornan JSON con estructura consistente
- ✅ Errores manejados con códigos HTTP apropiados (400, 404, 500)
- ✅ Validación de parámetros en todos los endpoints
