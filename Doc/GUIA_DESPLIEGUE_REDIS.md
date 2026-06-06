# Guía de Despliegue: Redis, Docker y Celery (Local y Nube)

Este documento detalla el proceso investigativo y técnico para habilitar el procesamiento asíncrono (Celery + Redis) en entornos de desarrollo (Windows/Local) y en producción (Nube).

---

## 1. ¿Por qué usamos Redis y Docker?
- **Redis** actúa como un *Message Broker* en memoria ultrarrápido. Django le envía mensajes ("Procesa este video"), y Celery los consume en segundo plano.
- **Docker** nos permite correr Redis de forma limpia y oficial en cualquier sistema operativo (especialmente en Windows, donde Redis no tiene una versión oficial nativa).

---

## 2. Entorno Local (Windows con Docker)

### Requisitos previos:
1. Instalar [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/).
2. Asegurarte de que esté corriendo (el icono de la ballena debe estar verde en la barra de tareas).

### Paso 1: Levantar Redis en Docker
Abre una terminal (PowerShell o CMD) y ejecuta un único comando:
```bash
docker run -d --name biopose-redis -p 6379:6379 redis:alpine
```
- `-d`: Corre en segundo plano (detached).
- `--name`: Le da el nombre "biopose-redis" a tu contenedor.
- `-p 6379:6379`: Expone el puerto 6379 (el de Redis) a tu computadora.
- `redis:alpine`: Descarga una versión de Redis ultraligera.

### Paso 2: Arrancar Celery
Abre **otra ventana de terminal**, entra primero a `backend/`, activa tu entorno virtual y arranca el trabajador:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A core worker -l info --pool=solo
```
*(Nota: En Windows, `--pool=solo` es obligatorio para que Celery funcione correctamente debido a cómo Windows maneja los procesos fork).*

Si aparece `Unable to load celery application. The module core was not found`, significa que el comando se ejecutó desde la raíz del repositorio o desde un directorio que no contiene el paquete `core`. La corrección es volver a `backend/` y ejecutar el comando desde allí.

---

## 3. Entorno de Producción (Despliegue en la Nube - Capa Gratuita)

Si deseas subir el backend de Biopose a Internet sin gastar dinero durante la etapa de pruebas, existen varias alternativas para desplegar el Broker (Redis) y el Worker (Celery).

### Opción A: AWS (Amazon Web Services) - Capa Gratuita (EC2)
Es el enfoque más robusto y común en la industria.
1. **Crear una instancia EC2 (t2.micro)**:
   - En AWS, lanza una instancia EC2 con **Ubuntu Server** (incluida en el Free Tier por 12 meses).
2. **Instalar Docker y Redis en EC2**:
   - Conéctate por SSH a tu instancia e instala Docker.
   - Ejecuta el mismo comando `docker run -d -p 6379:6379 redis:alpine`.
3. **Desplegar Django y Celery**:
   - Clona tu repositorio en la misma máquina EC2.
   - Usa `Supervisor` o `Systemd` para mantener vivos dos procesos:
     - `gunicorn core.wsgi:application` (Tu servidor Django)
     - `celery -A core worker -l info` (Tu Worker)
4. **Configuración `.env`**: `CELERY_BROKER_URL=redis://localhost:6379/0` (Ya que todo vive en la misma máquina).

### Opción B: Redis Serverless (Upstash) + Render
Si no quieres configurar servidores (EC2), puedes usar servicios completamente gestionados (Serverless).
1. **Redis Gestionado (Upstash)**:
   - Crea una cuenta gratis en [Upstash.com](https://upstash.com/).
   - Crea una base de datos Redis. Te dará una URL (ej. `rediss://default:contraseña@endpoint.upstash.io:6379`).
2. **Despliegue del Backend (Render.com)**:
   - Crea una cuenta en [Render](https://render.com/).
   - Crea un **Web Service** para Django.
   - Crea un **Background Worker** para Celery (Comando: `celery -A core worker -l info`).
3. **Variables de entorno**:
   - En Render, configura `CELERY_BROKER_URL` con la URL que te dio Upstash.

### Opción C: Railway.app o Fly.io
Plataformas todo-en-uno que te permiten desplegar bases de datos y código fácilmente.
1. En Railway, haces clic en "New Project" -> "Provision Redis".
2. Luego conectas tu repositorio de GitHub.
3. Railway automáticamente inyecta la URL de Redis como una variable de entorno `REDIS_URL`. En tu `settings.py` solo debes asegurarte de leerla:
   `CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')`.
