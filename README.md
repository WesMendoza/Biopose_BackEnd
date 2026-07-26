# Biopose BackEnd - Sistema Distribuido Django

Este es el backend principal del proyecto BioPose para detección y análisis de posturas y actitudes sospechosas (Violencia, Hurtos, Disturbios, Normal). La arquitectura está basada en **Django**, **Celery**, **PostgreSQL** e Inteligencia Artificial (YOLO + LSTM), todo desplegado en una infraestructura Cloud (AWS).

---

## ☁️ Infraestructura y Despliegue en AWS

El proyecto se encuentra integrado y desplegado con servicios en la nube para garantizar escalabilidad y seguridad:
- **Base de Datos:** PostgreSQL alojado en **AWS RDS**.
- **Almacenamiento Estático y Media:** Integración con **AWS S3** para alojar videos analizados e imágenes.
- **Frontend:** La aplicación cliente está alojada en **AWS Amplify** conectada por medio de configuración CORS segura.

## 🧠 Módulos de IA (Actitudes Sospechosas)

BioPose procesa video e imágenes en tiempo real y diferido utilizando:
- **YOLOv8** para la detección precisa del esqueleto (Keypoints) y seguimiento de múltiples personas (ByteTrack).
- **Redes Neuronales LSTM** para el análisis secuencial de los movimientos, permitiendo clasificar comportamientos sospechosos con alta precisión (Pelea, Disturbio).

---

## 🚀 Cómo Levantar el Proyecto Localmente

### 1. Requisitos Previos (Docker y Servidor Asíncrono)
Para manejar tareas pesadas (como el análisis de video con IA) sin bloquear la API, utilizamos un **Servidor Asíncrono (Celery)** apoyado por **Redis** como intermediario (Message Broker).

* **Python 3.12** instalado en tu sistema.
* **Docker Desktop:** Es necesario para levantar Redis en tu entorno de desarrollo, especialmente en Windows.
  1. Descarga e instala [Docker Desktop](https://www.docker.com/products/docker-desktop).
  2. Abre Docker Desktop y asegúrate de que el motor (Engine) inicie correctamente.
  3. Ejecuta el siguiente comando en tu terminal para descargar la imagen y levantar el servidor asíncrono en segundo plano:
     ```powershell
     docker run -d -p 6379:6379 --name redis-biopose redis
     ```

### 2. Variables de Entorno (`.env` vs `.env.local`)
El proyecto maneja dos archivos de variables de entorno para separar el entorno de despliegue del de desarrollo local.
Dentro de la carpeta `backend/`, asegúrate de tener:

* **`.env`** (Despliegue/Fallback): Contiene las variables del ambiente en AWS y tiene `DEBUG=False`.
* **`.env.local`** (Desarrollo): Archivo para correr el proyecto en tu máquina. Django buscará este archivo primero y lo priorizará. 

Ejemplo de un `.env.local`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=DbBioPose
DB_USER=postgres
DB_PASSWORD=12345
DB_SCHEMA=Dev
SECRET_KEY=django-insecure-test-key-please-change
DEBUG=True
LSTM_MODEL_PATH=resources/models/lstm_3clasesstride1.pt
LABEL_MAP_PATH=resources/models/label_map_3clases.json
```

### 3. Entorno Virtual y Dependencias
Abre una terminal en la carpeta `backend/`:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## ⚙️ Cómo Ejecutar los Servicios

El sistema distribuido requiere levantar dos procesos en terminales separadas (ambas con el entorno virtual activado y dentro de la carpeta `backend/`). Es crucial levantar el servidor asíncrono para que las funciones de IA operen correctamente:

**Terminal 1: Servidor Django (API REST Principal)**
```powershell
python manage.py runserver
```

**Terminal 2: Worker de Celery (Servidor Asíncrono)**
Este proceso se queda escuchando tareas pesadas en segundo plano. Cuando Django recibe un video, Celery toma la orden a través de Redis, levanta los modelos de IA y procesa el archivo:
```powershell
celery -A core worker -l info --pool=solo
```
*(Nota: El flag `--pool=solo` es estrictamente necesario en Windows para que la ejecución asíncrona no falle)*

---

## 📡 Endpoints Principales y Flujo

Todos los endpoints (excepto login) requieren enviar el token JWT en las cabeceras: `Authorization: Bearer <tu_token>`.

> [!NOTE]
> * Para una documentación exhaustiva e individualizada de todos los endpoints, Server-Sent Events, WebSockets y tareas asíncronas de este módulo, consulta la [Guía Detallada de Métodos de Análisis](Biopose_BackEnd/Doc/METODOS_ANALISIS.md) o en esta ruta levantando el proyecto [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/) o [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/).
> * Para ver los diagramas visuales interactivos de los flujos del sistema (Autenticación, Celery + Redis, Canvas y WebSockets), consulta los [Diagramas de Flujo de BioPose](Doc/DIAGRAMAS_FLUJO.md).

### A. Autenticación (Multi-tenant)
- **Login:** `POST /api/auth/login/` (Devuelve token de acceso).

### B. Análisis de Imágenes
- **Subir y procesar imagen:** `POST /api/analysis/media/images/upload/` (Responde con datos anatómicos al instante).

### C. Análisis de Videos de Actitudes Sospechosas (Asíncrono con Celery)
1. **Subir video:** `POST /api/analysis/media/videos/upload/` -> Responde `PENDING`
2. **Iniciar Procesamiento:** `POST /api/analysis/videos/{id}/process/` -> Encola tarea.
3. **Consultar Resultados:** `GET /api/analysis/videos/{id}/results/` -> Retorna resumen (Pelea/Disturbio) o estado `PROCESSING`.
4. **Obtener JSON de Keypoints:** `GET /api/analysis/videos/{id}/keypoints-json/` -> Coordenadas para renderizado Frontend.

---

## 🖌️ Instrucciones para el Frontend

Para optimizar rendimiento computacional, el backend **NO** devuelve un video MP4 pesado con los esqueletos dibujados. 
En su lugar, el backend entrega el archivo de video original sin procesar (`rutaArchivo`) y un archivo ligero (`rutaJsonKeypoints`). 
El frontend debe colocar un `<canvas>` sobre el video original, escuchar el evento `timeupdate` de HTML5 y pintar las líneas anatómicas (keypoints) extrayéndolas del JSON sincronizado.

---

## ⚡ Pruebas de Rendimiento en Vivo (Locust)

Hemos integrado un entorno de pruebas de estrés para medir el rendimiento de la API REST y el procesamiento asíncrono en Celery.

Para ver las instrucciones de configuración, credenciales y cómo ejecutar el dashboard en tiempo real, consulta la [Guía de Pruebas de Rendimiento](BIOPOSE/Biopose_BackEnd/backend/performance_tests/README.md).