# 🚀 Pruebas de Rendimiento en Vivo con Locust - BioPose BackEnd

Este directorio contiene la configuración y scripts para realizar **pruebas de rendimiento y estrés en vivo** en la API distribuida de BioPose. 

Para las pruebas, utilizamos **Locust**, un framework de pruebas de carga programable en Python que permite definir el comportamiento de los usuarios mediante código y monitorear los resultados en tiempo real desde un panel web.

---

## 📂 Contenido del Módulo

* `locustfile.py`: Script principal que simula usuarios virtuales autenticándose con JWT, realizando subidas de imágenes y ejecutando el flujo asíncrono de procesamiento de videos con YOLOv8/LSTM.
* `test_video_short.mp4` *(Recomendado)*: Debes colocar un video real muy corto en esta carpeta para que el pipeline de IA en Celery pueda procesarlo sin fallos de decodificación.

---

## ⚙️ Preparación del Entorno

### 1. Instalar dependencias
Dado que `locust` fue agregado al archivo general [requirements.txt](file:///d:/Daniel/Actividades/Python/Proyecto BIOPOSE/Biopose_BackEnd/backend/requirements.txt), puedes instalarlo asegurando que tu entorno virtual está activo y corriendo:

```powershell
# Activar entorno virtual (si no está activo)
.\venv\Scripts\Activate.ps1

# Instalar dependencias actualizadas
pip install -r requirements.txt
```

### 2. Configurar un Usuario de Prueba en Base de Datos
El script de pruebas necesita iniciar sesión para obtener un token JWT. Asegúrate de tener un usuario registrado y activo con estado `'A'` en tu base de datos de desarrollo. 

Puedes configurar las credenciales de este usuario de dos formas:

#### Opción A: Variables de entorno (Recomendado)
Configura las variables en tu terminal antes de lanzar Locust:
```powershell
$env:BIOPOSE_TEST_EMAIL="tu_usuario_prueba@correo.com"
$env:BIOPOSE_TEST_PASSWORD="tu_password_seguro"
```

#### Opción B: Modificar valores por defecto en el script
Abre [locustfile.py](file:///d:/Daniel/Actividades/Python/Proyecto BIOPOSE/Biopose_BackEnd/backend/performance_tests/locustfile.py) y edita las líneas `11` y `12`:
```python
CORREO = os.getenv("BIOPOSE_TEST_EMAIL", "tu_usuario_prueba@correo.com")
PASSWORD = os.getenv("BIOPOSE_TEST_PASSWORD", "tu_password_seguro")
```

### 3. Agregar Video Corto de Prueba (Evitar errores en YOLO)
El backend de BioPose procesa los videos usando OpenCV y YOLOv8 en segundo plano a través de Celery. Si subes datos aleatorios de relleno o un archivo corrupto, OpenCV fallará al decodificarlo y el flujo reportará `FAILED`.

* Consigue un video `.mp4` real muy corto (ej. **1 a 2 segundos**, baja resolución y pocos frames).
* Guárdalo dentro de la carpeta `backend/performance_tests/` con el nombre `test_video_short.mp4`.
* *Si no lo agregas, el script usará datos binarios ficticios; podrás probar el endpoint de subida, pero el procesamiento en Celery fallará.*

---

## 🏃 Cómo Ejecutar las Pruebas en Vivo

### Paso 1: Levantar los servicios de BioPose
Asegúrate de tener corriendo los tres servicios esenciales en terminales separadas dentro de `backend/`:..

   docker run -d -p 6379:6379 --name redis-biopose redis

1. **Redis (Broker de Celery):**
   ```powershell
   docker start redis-biopose
   ```
2. **Servidor Django (API REST):**
   ```powershell
   python manage.py runserver
   ```
3. **Worker Celery (IA YOLO/LSTM):**
   ```powershell
   celery -A core worker -l info --pool=solo
   ```

### Paso 2: Iniciar Locust
Abre una **cuarta terminal** en la carpeta `backend/`, activa el entorno virtual y ejecuta:
```powershell
locust -f performance_tests/locustfile.py
```

### Paso 3: Configurar la prueba en la interfaz Web
Una vez iniciado Locust, abre tu navegador y ve a:
👉 **`http://localhost:8089/`**

Completa el formulario inicial:
* **Number of users:** Cantidad total de usuarios simulados en concurrencia (ej. `10`).
* **Spawn rate:** Cantidad de usuarios que se crean por segundo hasta llegar al total (ej. `1`).
* **Host:** Dirección local de tu API de Django: **`http://localhost:8000`**

Haz clic en **Start swarming**.

---

## 📊 ¿Qué monitorear durante la prueba?

1. **Dashboard de Locust (Pestañas `Statistics` y `Charts`):**
   * **RPS (Requests Per Second):** Cantidad de peticiones que el backend procesa por segundo.
   * **Response Time (Percentiles 95% y 99%):** El tiempo que tarda la API en responder al usuario. Si sube de golpe, indica saturación.
   * **Failures:** Verifica si hay errores `401` (problemas de token JWT), `400` o `500` (errores internos).
   
2. **Consola del Worker de Celery:**
   * Observa con qué velocidad se van encolando y procesando los análisis de video (`process_video_task`).
   * Si aumentas la cantidad de usuarios en Locust y ves que Celery empieza a tardar más por video o a acumular tareas pendientes, habrás encontrado la **capacidad máxima de procesamiento de IA de tu servidor actual**.
