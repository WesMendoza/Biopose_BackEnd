# Biopose BackEnd - Sistema Distribuido Django

Este es el **nuevo backend principal** del proyecto BioPose para detección y análisis de posturas y comportamientos humanos (Pelea, Disturbio, Normal). Hemos migrado desde una arquitectura monolítica Flask hacia un sistema distribuido basado en **Django**, **Celery** y **PostgreSQL**.

---

## 📊 Estado Actual del Proyecto (Migración)

| Fase | Componente | Estado |
|------|-----------|--------|
| **1** | Servicios de IA encapsulados (YOLO, LSTM) | ✅ Completado |
| **2** | Modelos Django (ORM) y Base de Datos | ✅ Completado |
| **3** | API REST e Inferencia de Imágenes | ✅ Completado |
| **6** | Autenticación JWT y Usuarios (Multi-tenant) | ✅ Completado |
| **4** | Celery + Redis (Procesamiento de Video) | ⏳ En Pruebas |
| **5** | WebSocket (Django Channels) | ⏳ Pendiente |
| **7** | Configuración CORS | ⏳ Pendiente |

---

## 🚀 Cómo Levantar el Proyecto Localmente

### 1. Requisitos Previos
* **Python 3.10+** instalado.
* **PostgreSQL** ejecutándose.
* **Redis** instalado y ejecutándose en el puerto 6379 (usa Docker Desktop si estás en Windows: `docker run -d -p 6379:6379 redis`).

### 2. Base de Datos
Crea una base de datos en PostgreSQL (ej: `DbBioPose`).
Crea el esquema `"Dev"` y corre el script de inicialización:
```sql
CREATE SCHEMA IF NOT EXISTS "Dev";
-- Ejecuta el contenido de backend/scripts/db/create/Esquema BD.sql
```

### 3. Variables de Entorno (`.env`)
Dentro de la carpeta `backend/`, crea un archivo `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=DbBioPose
DB_USER=postgres
DB_PASSWORD=tu_contraseña_secreta
DB_SCHEMA=Dev
SECRET_KEY=django-insecure-test-key
DEBUG=True
LSTM_MODEL_PATH=resources/models/lstm_3clasesstride1.pt
LABEL_MAP_PATH=resources/models/label_map_3clases.json
```

### 4. Entorno Virtual y Dependencias
Abre una terminal en la carpeta `backend/`:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## ⚙️ Cómo Ejecutar los Servicios

El sistema distribuido requiere levantar dos procesos en terminales separadas (ambas con el entorno virtual activado y dentro de la carpeta `backend/`):

**Terminal 1: Servidor Django (API REST)**
```powershell
python manage.py runserver
```

**Terminal 2: Worker de Celery (Procesamiento de Video)**
```powershell
celery -A core worker -l info --pool=solo
```

---

## 📡 Cómo Consumir los Endpoints Principales

Todos los endpoints (excepto login) requieren enviar el token JWT en las cabeceras: `Authorization: Bearer <tu_token>`.

### A. Autenticación (Fase 6)
1. **Login:** `POST /api/auth/login/`
   * Body: `{"correo": "admin@empresa.com", "password": "123"}`
   * Responde: `{"access": "eyJ...", "refresh": "eyJ..."}`

### B. Análisis de Imágenes (Fase 3)
1. **Subir y procesar imagen:** `POST /api/analysis/media/images/upload/`
   * *Form-Data*: `image` (archivo)
   * Responde: Datos anatómicos y bounding boxes al instante.

### C. Análisis de Videos Asíncrono (Fase 4 - En Pruebas)
1. **Subir video:** `POST /api/analysis/media/videos/upload/`
   * *Form-Data*: `video` (archivo mp4)
   * Responde: HTTP 201 con `{"idVideoUpload": 1, "estado": "PENDING"}`

2. **Iniciar Procesamiento:** `POST /api/analysis/videos/1/process/`
   * Responde: HTTP 202 Accepted. Esto encola la tarea en Celery.

3. **Consultar Resultados:** `GET /api/analysis/videos/1/results/`
   * *Si no ha terminado:* Responde estado `"PROCESSING"`.
   * *Si terminó:* Responde HTTP 200 con el reporte de eventos (Pelea, Disturbio) y un campo nuevo llamado `rutaJsonKeypoints` (ej. `reports/keypoints_video_1.json`).

---

## 🖌️ Instrucciones para el Desarrollador Frontend

Para optimizar rendimiento computacional, el backend **NO** devuelve un video MP4 pesado con los esqueletos dibujados cuadro por cuadro. 

**La nueva estrategia vectorial (Canvas):**
1. Al consultar los resultados del video, el backend te entregará el archivo de video original sin procesar (`rutaArchivo`) y un archivo ligero (`rutaJsonKeypoints`) generado por Celery.
2. Descarga el JSON de keypoints, que contiene un array con los eventos por segundo.
3. En el `index.html`, superpón una etiqueta `<canvas>` transparente encima de la etiqueta `<video>`.
4. Mediante JavaScript, escucha el evento `timeupdate` del reproductor de video, busca el `timestamp_sec` correspondiente en tu JSON, y dibuja las líneas anatómicas (`ctx.lineTo`) sobre el `<canvas>` en tiempo real.

---

## 📚 Documentación Detallada y Especificaciones Técnicas

El proyecto mantiene un historial riguroso de cada fase completada. Para entender las decisiones arquitectónicas profundas, consulta los siguientes documentos:

### [FASE_1_COMPLETADA.md](backend/FASE_1_COMPLETADA.md) (Servicios de IA)
* **Logro:** Desacoplamiento total de los modelos (YOLOv8, LSTM) del framework web.
* **Detalle:** Se movieron los scripts antiguos del monolito a la nueva carpeta `backend/services/`. Se ajustaron para que no dependan del objeto `app` de Flask, permitiendo que puedan ejecutarse en procesos separados (como lo hace Celery hoy en día).

### [FASE_2_COMPLETADA.md](backend/FASE_2_COMPLETADA.md) (Esquema de BD y ORM)
* **Logro:** Diseño de Base de Datos y Modelos Django (`managed = False`).
* **Especificación Estricta:** Se estableció el uso riguroso de **camelCase** tanto en las tablas físicas como en las propiedades de Django ORM. Las tablas en PostgreSQL se crean explícitamente entre comillas (ej. `"analysisImageUpload"`) para forzar la capitalización.

### [FASE_3_COMPLETADA.md](backend/FASE_3_COMPLETADA.md) (API REST Básica)
* **Logro:** Reemplazo de los 37 endpoints enrevesados de Flask por 9 endpoints RESTful limpios.
* **Detalle:** Incluye todo el flujo de subida de **Imágenes** y procesamiento sincrónico. Se separó la lógica en la app `analysis`. También puedes consultar la [FASE_3_ESPECIFICACION.md](Doc/FASE_3_ESPECIFICACION.md) para ver el mapeo exacto de las rutas antiguas vs nuevas.

### [FASE_4_COMPLETADA.md](backend/FASE_4_COMPLETADA.md) (Celery + Redis)
* **Logro:** Procesamiento asíncrono pesado.
* **Detalle:** Se implementó el patrón *Background Worker* para evitar que el servidor de Django se bloquee. Aquí se consolidó la generación del JSON dinámico en lugar de renderizar videos completos en disco.

### [FASE_6_COMPLETADA.md](backend/FASE_6_COMPLETADA.md) (Autenticación y Roles)
* **Logro:** Sistema Multi-Tenant seguro.
* **Detalle:** Se abandonaron las sesiones antiguas y se migró a **JSON Web Tokens (JWT)**. Las apps `users`, `gestionEmpresas` y `authentication` ahora manejan borrado lógico y permisos granulares independientes por empresa.

### [ESPECIFICACION_DESARROLLO.md](Doc/ESPECIFICACION_DESARROLLO.md)
* **Manual de Oro:** Contiene los principios SOLID que rigen el proyecto, el porqué de la arquitectura modular, las convenciones de nomenclatura (camelCase transversal) y la prohibición de lógica de negocio dentro de las Vistas (Views).

## 📝 Notas Importantes

- **El código del Tesis se mantiene intacto** durante la migración para permitir rollback
- **Cada fase es independiente** y se puede validar antes de continuar
- **El README se actualiza** conforme avanza cada fase
- **Documentación es viva**: Los archivos en `Doc/` se actualizan con cambios arquitectónicos

---