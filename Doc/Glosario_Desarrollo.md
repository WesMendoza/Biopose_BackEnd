## 📚 Glosario de Términos Clave

Este glosario explica los términos técnicos que se usan en la migración. La idea es que cada palabra tenga un significado claro, corto y útil para el trabajo diario.

### Frameworks y API

| Término | Significado |

|-------------------|----------------------------------------------------------------------------------------------------|
| Django : Framework web de Python para construir aplicaciones con base de datos, autenticación y administración. |
| Django REST Framework (DRF) : Extensión de Django para construir APIs REST de forma rápida y estructurada. |
| ViewSet : Clase de DRF que agrupa operaciones sobre un recurso, como listar, crear, actualizar y eliminar. |
| Serializer : Componente que convierte datos de modelos Python a JSON y viceversa. |
| ORM : Capa que permite trabajar con la base de datos usando objetos Python en lugar de SQL directo. |

### Comunicación en tiempo real y tareas

| Término | Significado |
|-------------------|----------------------------------------------------------------------------------------------------|
| WebSocket : Protocolo de comunicación bidireccional en tiempo real entre cliente y servidor. |
| Django Channels : Librería que agrega soporte para WebSocket y procesos asíncronos en Django. |
| Consumer : Clase que maneja conexiones WebSocket, similar a una vista pero para sockets. |
| Celery : Sistema para ejecutar tareas pesadas en segundo plano sin bloquear la API. |
| Task : Función que Celery ejecuta de forma asíncrona en un worker. |
| Broker : Intermediario que recibe y distribuye tareas a los workers, por ejemplo Redis. |
| Redis : Base de datos en memoria usada como broker, caché o almacenamiento temporal. |

### Seguridad y arquitectura

| Término | Significado |
|-------------------|----------------------------------------------------------------------------------------------------|
| JWT Token : Token firmado usado para autenticación sin sesión tradicional. |
| CORS : Mecanismo que controla qué orígenes pueden consumir una API desde el navegador. |
| Microservicios :  Arquitectura donde el sistema se divide en servicios independientes y especializados. |
| Migration : Cambio versionado en la estructura de la base de datos administrado por Django. |

### Dominio del proyecto

| Término | Significado |
|-------------------|----------------------------------------------------------------------------------------------------|
| Behavior : Comportamiento detectado en video, como pelea, disturbio o actividad normal. |
| Keypoints : Puntos clave del cuerpo humano, como cabeza, hombros, codos o rodillas. |
| Pose Detection : Proceso de detectar la postura del cuerpo en una imagen o video. |

### Términos añadidos (Fase 2)

| Término | Significado |
|-------------------|----------------------------------------------------------------------------------------------------|
| VideoUpload : Metadatos del vídeo subido (nombre original, ruta, tamaño, duración, estado, celeryTaskId, timestamps). Permite auditoría y re-procesos. |
| DetectionEvent : Evento detectado dentro de un video (tipo, confianza, frame inicio/fin, tiempos, personas involucradas, detalles JSON). |
| PersonKeypoints : Keypoints (JSON) por persona y frame asociados a un `DetectionEvent`. Útil para reproducción y re-entrenamiento. |
| AnalysisReport : Resumen agregado generado por video: totales, conteos por tipo, estadísticas, resumen JSON, timestamps de generación y actualización. Fuente para dashboards. |
| systemParameter : Tabla de parámetros globales de la aplicación (umbrales por defecto, flags). No debe duplicar parámetros por empresa. |
| parametrosCabecera / parametroDetalle : Tablas maestras de configuración por empresa. Recomendadas para configuraciones con scope por `idEmpresa`. |
| JSONB / GIN : Tipos y índices PostgreSQL recomendados para búsquedas eficientes dentro de campos JSON. |
| idEmpresa (tenant) |:Identificador de la empresa/tenant. Usado para agregación, permisos y multi-tenancy. |
| Audit fields : Campos de auditoría comunes: `usuarioCreacion`, `fechaCreacion`, `usuarioModificacion`, `fechaModificacion`. Deben existir en tablas que requieren trazabilidad. |

### Términos añadidos (Fase 3)

| Término | Significado |
|-------------------|----------------------------------------------------------------------------------------------------|
| Serializer : Componente DRF que convierte modelos Django a JSON y valida datos de entrada. Ejemplo: VideoUploadSerializer transforma VideoUpload model a JSON. |
| ViewSet : Clase DRF que agrupa operaciones CRUD sobre un recurso (create, read, update, delete, custom actions). |
| RESTful : Arquitectura que sigue convenciones HTTP: GET (lectura), POST (creación), PUT/PATCH (actualización), DELETE (eliminación). |
| HTTP 202 Accepted : Código que indica que la solicitud fue aceptada pero aún se está procesando. Ideal para operaciones asíncronas largas. |
| Server-Sent Events (SSE) : Protocolo HTTP unidireccional para transmitir eventos del servidor al cliente. Más simple que WebSocket, sin necesidad de bidireccional. |
| Multipart Form Data : Formato para enviar archivos + datos en formularios. Usado en endpoints de upload de imágenes y videos. |
| YOLO (You Only Look Once) : Modelo de detección de objetos. YOLOv8s-pose detecta 17 puntos clave del cuerpo humano (keypoints) en formato COCO. |
| COCO Format (Keypoints) : Estándar para representar 17 puntos clave: nariz, ojos, orejas, hombros, codos, muñecas, caderas, rodillas, tobillos. Cada punto tiene (x, y, z, confidence). |
| LSTM (Long Short-Term Memory) : Red neuronal recurrente para secuencias. En BioPose, analiza secuencias de keypoints para detectar comportamientos (DISTURBIO, PELEAR). |
| Behavior Detection : Detección de comportamientos/acciones a partir de pose (por ejemplo, pelea, disturbio, actividad normal). Usa LSTM en ventanas de 32 frames. |
| Confidence / Confianza : Probabilidad que asigna el modelo. Ejemplo: YOLO retorna confidence para cada keypoint. LSTM retorna confidence para cada detección (0-1 escala). |
| Stream / Streaming : Transmisión continua de datos. SSE para progreso de procesamiento. WebSocket para tiempo real bidireccional. |
| Endpoint : Ruta URL + método HTTP que expone una funcionalidad. Ejemplo: `POST /api/analysis/videos/upload/` es un endpoint. |
| Status Codes HTTP : Códigos de respuesta: 200 OK, 202 Accepted, 400 Bad Request, 404 Not Found, 500 Internal Server Error, etc. |
| File Upload : Carga de archivos desde cliente. Usa `multipart/form-data`. Max 50MB en BioPose legacy. |
| Media Files : Archivos generados/subidos por usuarios (imágenes, videos). En Django, se almacenan en `MEDIA_ROOT` (antes: `Tesis/src/static/`, ahora: `backend/media/`). |
| Image Processing : Procesamiento de imágenes (redimensionamiento, detección de pose, conversión de formato). Usa YOLO para keypoints. |
| Video Processing : Procesamiento de videos (extracción de frames, análisis de comportamiento por frame). Usa LSTM para detección de eventos. |
| Frame : Un fotograma individual de un video. En BioPose, se procesan frames para detectar pose y comportamiento. |
| FPS (Frames Per Second) : Fotogramas por segundo. Usado para muestreo (ejemplo: procesar cada 5º frame) y extracción de imágenes de videos. |
| Query Parameters : Parámetros en la URL (después de `?`). Ejemplo: `/stream/?mode=operativo&dimension=2D`. |
| Path Parameters : Parámetros en la ruta. Ejemplo: `/videos/{id}/` donde `{id}` es path parameter. |
| Request Body : Datos enviados en el cuerpo de una solicitud. Puede ser JSON, multipart form-data, etc. |
| Response Body : Datos retornados por el servidor. Generalmente JSON en REST APIs. |
| Stateless : API sin estado: cada solicitud es independiente, no depende de solicitudes previas. REST es stateless. |
| Idempotent : Operación que produce el mismo resultado si se ejecuta múltiples veces. GET y DELETE son idempotentes. |



### Nota de uso

- Si un término aparece en `README.md`, este glosario debe ayudar a interpretarlo.
- Si se agregan nuevos conceptos técnicos, conviene ampliar este documento antes de cerrar una fase.
- Los términos deben mantenerse cortos, consistentes y sin definiciones duplicadas.