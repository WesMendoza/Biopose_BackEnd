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


### Nota de uso

- Si un término aparece en `README.md`, este glosario debe ayudar a interpretarlo.
- Si se agregan nuevos conceptos técnicos, conviene ampliar este documento antes de cerrar una fase.
- Los términos deben mantenerse cortos, consistentes y sin definiciones duplicadas.