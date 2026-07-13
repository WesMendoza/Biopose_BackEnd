# Documentación de Métodos de Análisis (`apps.analysis`)

Este documento detalla los endpoints HTTP (API REST), WebSockets (Django Channels) y tareas en segundo plano (Celery) implementados en el módulo de análisis (`apps.analysis`).

---

## 📂 Índice
1. [API de Gestión de Archivos (Media)](#1-api-de-gestión-de-archivos-media)
2. [API de Estimación de Pose en Imágenes (Pose)](#2-api-de-estimación-de-pose-en-imágenes-pose)
3. [API de Procesamiento y Clasificación de Video (Behavior)](#3-api-de-procesamiento-y-clasificación-de-video-behavior)
4. [API de Detección en Tiempo Real (Live - SSE & WebSockets)](#4-api-de-detección-en-tiempo-real-live---sse--websockets)
5. [Tareas en Segundo Plano (Celery Tasks)](#5-tareas-en-segundo-plano-celery-tasks)

---

## 1. API de Gestión de Archivos (Media)
Implementada en [media/views.py](/Biopose_BackEnd/backend/apps/analysis/api/media/views.py) y enrutada en [media/urls.py](/Biopose_BackEnd/backend/apps/analysis/api/media/urls.py).

### A. Subir Imagen
* **URL:** `/api/analysis/media/images/upload/`
* **Método:** `POST`
* **Parser:** `MultipartForm`
* **Descripción:** Sube una imagen en bruto al servidor y registra un objeto `ImageUpload` en la base de datos con estado `PENDING`. Limita el peso a un máximo de 10 MB.
* **Payload (Body - form-data):**
  * `image` (File): Archivo de la imagen (`.png`, `.jpg`, `.jpeg`).
* **Respuesta (201 Created):**
  ```json
  {
    "idImageUpload": 1,
    "nombreOriginal": "mi_foto.jpg",
    "rutaArchivoOriginal": "images/uploads/img_e23a41bc.jpg",
    "tamanioBytes": 204850,
    "estado": "PENDING"
  }
  ```

### B. Subir Video
* **URL:** `/api/analysis/media/videos/upload/`
* **Método:** `POST`
* **Parser:** `MultipartForm`
* **Descripción:** Sube un video en bruto al servidor y registra un objeto `VideoUpload` en la base de datos con estado `PENDING`. Limita el peso a 50 MB. Dispara de forma pasiva una tarea de limpieza de archivos obsoletos.
* **Payload (Body - form-data):**
  * `video` (File): Archivo de video (`.mp4`, `.webm`, etc.).
* **Respuesta (201 Created):**
  ```json
  {
    "idVideoUpload": 10,
    "nombreOriginal": "grabacion_seguridad.mp4",
    "rutaArchivo": "videos/uploads/vid_8fb39d10.mp4",
    "tamanioBytes": 12450890,
    "estado": "PENDING"
  }
  ```

### C. Eliminar / Limpiar Video y Reporte
* **URL:** `/api/analysis/media/videos/<int:video_id>/`
* **Método:** `DELETE`
* **Descripción:** Elimina físicamente del almacenamiento del servidor el video original (`.mp4`), su respectivo archivo de keypoints JSON (`.json`) y el registro de la base de datos.
* **Respuesta (200 OK):**
  ```json
  {
    "message": "Archivos y datos destruidos correctamente"
  }
  ```

---

## 2. API de Estimación de Pose en Imágenes (Pose)
Implementada en [pose/views.py](/Biopose_BackEnd/backend/apps/analysis/api/pose/views.py) y enrutada en [pose/urls.py](/Biopose_BackEnd/backend/apps/analysis/api/pose/urls.py).

### A. Procesar Imagen con YOLOv8-pose
* **URL:** `/api/analysis/pose/image/<int:image_id>/process/`
* **Método:** `POST`
* **Descripción:** Toma la imagen con el ID especificado, la procesa mediante YOLOv8-pose para extraer los puntos clave (keypoints) de las personas detectadas, genera una imagen procesada con el esqueleto dibujado en `media/images/processed/` y un archivo JSON de reporte.
* **Respuesta (200 OK):**
  ```json
  {
    "success": true,
    "model_used": "yolov8s-pose",
    "position": "unknown",
    "persons_detected": 1,
    "processed_image_path": "images/processed/pose_f3b928ec.jpg",
    "persons": [
      {
        "person_id": 0,
        "bbox": { "x1": 0, "y1": 0, "x2": 0, "y2": 0 },
        "keypoints": [
          { "id": 0, "name": "nose", "x": 340.5, "y": 150.2, "confidence": 0.95 }
          // ... 17 puntos COCO totales
        ]
      }
    ]
  }
  ```

### B. Descargar Dataset de Imagen Única
* **URL:** `/api/analysis/pose/image/<int:image_id>/save-to-disk/`
* **Método:** `POST`
* **Descripción:** Genera un archivo ZIP descargable que contiene la imagen y el archivo JSON con los keypoints. Posterior al empaquetamiento, elimina físicamente los archivos del servidor y remueve el registro de la base de datos para ahorrar espacio.
* **Payload (Body - JSON):**
  * `results` (Object): Los keypoints (editados o finales) devueltos por el frontend.
* **Respuesta (200 OK):**
  * Retorna un archivo binario ZIP: `Dataset_Imagen_<image_id>.zip`

### C. Descargar Dataset por Lotes (Batch)
* **URL:** `/api/analysis/pose/batch/save-to-disk/`
* **Método:** `POST`
* **Descripción:** Agrupa un conjunto de imágenes editadas por el usuario en el frontend, las comprime en un único archivo ZIP estructurado y limpia físicamente todos los archivos asociados en el servidor.
* **Payload (Body - JSON):**
  ```json
  {
    "batch": [
      {
        "imageId": 1,
        "results": { ... }
      },
      {
        "imageId": 2,
        "results": { ... }
      }
    ]
  }
  ```
* **Respuesta (200 OK):**
  * Retorna un archivo binario ZIP: `Dataset_Lote_<cantidad>_Imagenes.zip`

### D. Eliminar Imagen
* **URL:** `/api/analysis/pose/image/<int:image_id>/`
* **Método:** `DELETE`
* **Descripción:** Destruye físicamente la imagen original, procesada, el JSON de reportes y el registro de base de datos asociado.

### E. Listar Archivos Locales del Servidor
* **URL:** `/api/analysis/pose/local-files/`
* **Método:** `POST`
* **Descripción:** Lista los archivos de imagen existentes dentro del subdirectorio "Imagen" de la ruta especificada en el servidor.
* **Payload (Body - JSON):**
  ```json
  {
    "target_path": "D:/mi_proyecto/dataset"
  }
  ```
* **Respuesta (200 OK):**
  ```json
  [
    { "id": "0001.jpg", "name": "0001.jpg" },
    { "id": "0002.jpg", "name": "0002.jpg" }
  ]
  ```

### F. Obtener Imagen Local y JSON
* **URL:** `/api/analysis/pose/local-file-data/`
* **Método:** `POST`
* **Descripción:** Convierte una imagen local a Base64 y extrae sus keypoints del JSON correspondiente. Maneja tanto imágenes estáticas como fotogramas específicos de video (`_frame_`).
* **Payload (Body - JSON):**
  ```json
  {
    "target_path": "D:/mi_proyecto/dataset",
    "file_name": "0001.jpg"
  }
  ```
* **Respuesta (200 OK):**
  ```json
  {
    "image_b64": "data:image/jpeg;base64,...",
    "json_data": {
      "model_used": "yolov8s-pose",
      "persons_detected": 1,
      "persons": [...]
    }
  }
  ```

---

## 3. API de Procesamiento y Clasificación de Video (Behavior)
Implementada en [behavior/views.py](/Biopose_BackEnd/backend/apps/analysis/api/behavior/views.py) y enrutada en [behavior/urls.py](/Biopose_BackEnd/backend/apps/analysis/api/behavior/urls.py).

### A. Iniciar Procesamiento de Video (Asíncrono)
* **URL:** `/api/analysis/videos/<int:video_id>/process/`
* **Método:** `POST`
* **Descripción:** Envía una tarea asíncrona a Celery para que procese el video de forma exhaustiva con YOLO (Detección de Pose) y el clasificador LSTM (Detección de Violencia/Disturbios/Hurtos/Normal).
* **Payload (Body - JSON - Opcionales):**
  * `mode` (String): `'operativo'` (default) | `'analitico'` | `'debug'`.
  * `dimension` (String): `'2D'` (default) | `'3D'`.
  * `fps_skip` (Integer): Fotogramas a saltar para optimizar procesamiento (default: `5`).
  * `confidence_threshold` (Float): Umbral mínimo de detección (default: `0.75`).
  * `analysis_type` (String): `'multipersona'` (default) | `'individual'`.
* **Respuesta (202 Accepted):**
  ```json
  {
    "id": 10,
    "status": "processing",
    "task_id": "9a12b3c4-e8f9-40ab-bc11-a83d65b128fd",
    "message": "Video en procesamiento asíncrono. Puedes consultar progreso luego."
  }
  ```

### B. Obtener Resultados del Reporte de Video
* **URL:** `/api/analysis/videos/<int:video_id>/results/`
* **Método:** `GET`
* **Descripción:** Devuelve el resumen estadístico e información general del análisis del video una vez completado.
* **Respuestas:**
  * **202 Accepted (Aún procesando):**
    ```json
    { "id": 10, "status": "processing", "message": "El procesamiento aún está en curso." }
    ```
  * **200 OK (Completado):**
    ```json
    {
      "id": 10,
      "status": "completed",
      "total_frames": 300,
      "duration_seconds": 10.0,
      "processing_time_seconds": 3.45,
      "ruta_json_keypoints": "reports/keypoints_video_10.json",
      "analysis_report": {
        "total_detections": 2,
        "detections_by_type": { "PELEAR": 1, "DISTURBIO": 0 },
        "average_confidence": 0.88
      }
    }
    ```

### C. Obtener JSON Completo de Keypoints del Video
* **URL:** `/api/analysis/videos/<int:video_id>/keypoints-json/`
* **Método:** `GET`
* **Descripción:** Retorna el contenido completo del archivo JSON con los keypoints obtenidos fotograma por fotograma para propósitos de renderizado en el Frontend.
* **Respuesta (200 OK):**
  ```json
  {
    "id": 10,
    "status": "completed",
    "report_id": 5,
    "ruta_json_keypoints": "reports/keypoints_video_10.json",
    "keypoints": {
      "frames": [
        {
          "frame_index": 0,
          "timestamp_sec": 0.0,
          "keypoints_json": [...]
        }
      ],
      "detections": [...]
    }
  }
  ```

### D. Descargar Dataset de Video y Extraer Fotogramas en Caliente
* **URL:** `/api/analysis/videos/<int:video_id>/save-to-disk/`
* **Método:** `POST`
* **Descripción:** Genera un archivo ZIP descargable que contiene el JSON de keypoints y los fotogramas del video extraídos *al vuelo* desde la RAM sin tocar disco del servidor (usando OpenCV en buffer). Posterior a esto, limpia físicamente el video, JSONs y base de datos.
* **Payload (Body - JSON):**
  * `results` (Object): JSON de keypoints modificado por el frontend.
  * `width` (Integer - Opcional): Ancho para redimensionar los fotogramas guardados.
  * `height` (Integer - Opcional): Alto para redimensionar los fotogramas guardados.
* **Respuesta (200 OK):**
  * Retorna un archivo binario ZIP: `Dataset_VideoFrames.zip`

---

## 4. API de Detección en Tiempo Real (Live - SSE & WebSockets)
Implementada en [live/views.py](/Biopose_BackEnd/backend/apps/analysis/api/live/views.py) (para SSE) y [live/consumers.py](/Biopose_BackEnd/backend/apps/analysis/api/live/consumers.py) (para WebSockets).

### A. Stream en Vivo vía Server-Sent Events (SSE)
* **Endpoint SSE (Individual):** `/api/analysis/live/stream/`
* **Endpoint SSE (Multipersona):** `/api/analysis/live/stream-multiperson/`
* **Método:** `GET`
* **Query Parameters:**
  * `fps_skip` (Integer): default `3`.
  * `dimension` (String): `'2D'` | `'3D'`.
  * `source` (String): `'local'` (Webcam del servidor) | `'remote'` (Cámara remota).
  * `url` (String): URL RTSP o HTTP si `source=remote`.
  * `mode` (String - Solo en multipersona): `'operativo'` | `'analitico'` | `'debug'`.
* **Descripción:** Mantiene una conexión HTTP abierta transmitiendo los frames decodificados en Base64 junto a las detecciones de pose y actitudes sospechosas en tiempo real mediante formato SSE (`data: ...`).

### B. Canales WebSocket (Detección Interactiva)
Enrutados en [live/routing.py](/Biopose_BackEnd/backend/apps/analysis/api/live/routing.py).

#### 1. Detección Individual
* **Path:** `ws/live-detection/`
* **Descripción:** El cliente (navegador) transmite periódicamente fotogramas capturados localmente codificados en Base64, y el backend responde con los keypoints y la imagen procesada.
* **Formato del mensaje enviado (Client -> Server):**
  ```json
  {
    "frame": "iVBORw0KGgoAAAANS...", // Base64 de la imagen
    "fps_skip": 3,
    "mode": "2D"
  }
  ```
* **Formato del mensaje recibido (Server -> Client):**
  ```json
  {
    "type": "result",
    "frame": "data:image/jpeg;base64,...",
    "detections": [...],
    "num_people": 1,
    "realtime_behaviors": ["NORMAL"],
    "total_detections": 12
  }
  ```

#### 2. Detección Multipersona
* **Path:** `ws/live-action-multiperson/`
* **Descripción:** Variante del WebSocket diseñada para detectar actitudes sospechosas en múltiples personas interactuando concurrentemente dentro del mismo encuadre.
* **Formato del mensaje enviado (Client -> Server):**
  ```json
  {
    "frame": "...",
    "fps_skip": 3,
    "mode": "2D",
    "visual_mode": "Modo Analítico (Esqueletos)" // 'operativo' | 'analitico' | 'debug'
  }
  ```
* **Formato del mensaje recibido (Server -> Client):**
  *(Idéntica estructura con soporte para múltiples bounding boxes y esqueletos estructurados).*

---

## 5. Tareas en Segundo Plano (Celery Tasks)
Definidas en [tasks.py](/Biopose_BackEnd/backend/apps/analysis/tasks.py).

### A. `process_video_task`
* **Uso:** Procesamiento de video asíncrono y clasificación LSTM.
* **Funcionamiento:**
  1. Cambia el estado del video en BD a `PROCESSING`.
  2. Invoca el motor de procesamiento (individual o multipersona).
  3. Escribe los keypoints en un archivo JSON físico temporal en `media/reports/keypoints_video_<id>.json`.
  4. Registra los resultados detallados en el modelo `AnalysisReport` (BD).
  5. Actualiza el estado del video a `COMPLETED` o `FAILED` en caso de error.

### B. `cleanup_orphaned_media_task`
* **Uso:** Tarea pasiva y periódica para liberar recursos en el disco de AWS.
* **Funcionamiento:**
  1. Escanea archivos de `VideoUpload` e `ImageUpload` con fecha de creación mayor a **1 hora**.
  2. Borra los archivos multimedia originales e intermedios del disco local/servidor.
  3. Elimina los reportes JSON físicos generados de la carpeta `media/reports/`.
  4. Remueve los registros obsoletos correspondientes de la base de datos.
