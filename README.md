# Biopose BackEnd - Sistema Distribuido Django

## 📋 Descripción General

Este es el **nuevo backend principal** del proyecto BioPose para detección y análisis de posturas humanas. Estamos en proceso de **migración incremental** desde una arquitectura monolítica Flask hacia un sistema distribuido basado en **Django**, que separa responsabilidades en capas bien definidas y permite escalabilidad horizontal.

### Objetivo de la Migración

Transformar la aplicación actual (monolito Flask en `Tesis/src/`) hacia una arquitectura moderna donde:
- 🔧 **Django** maneja lógica de negocio, autenticación y API REST
- 🤖 **Servicios de IA** encapsulados e independientes (pose, comportamiento, 3D)
- ⚡ **Celery + Redis** procesan tareas pesadas de forma asíncrona
- 🔌 **WebSocket (Channels)** transmite eventos en tiempo real
- 📊 **PostgreSQL** almacena datos con migraciones versionadas
- 🎨 **Frontend** separado que consume API permitiendo exponer los endpoints sin problemas de CORS

### 🏛️ Tipo de Arquitectura

Esta migración implementa una **Arquitectura Modular Distribuida con patrón de Servicios Encapsulados**, caracterizada por:

- **Separación de Responsabilidades**: Cada componente (Django, Servicios IA, Celery, WebSocket) tiene un rol específico
- **Desacoplamiento**: Los servicios de IA son independientes del framework web (podrían ejecutarse en máquinas separadas)
- **Event-Driven**: Celery + WebSocket permiten comunicación asíncrona y notificaciones en tiempo real
- **Escalabilidad Horizontal**: Cada capa puede escalarse según demanda (más workers Celery, más réplicas del backend, etc.)
- **Contrato Claro**: API REST + WebSocket definen contratos explícitos entre componentes

**Comparación con monolito Flask:**
- ❌ **Antes**: Una sola máquina, un solo proceso, lógica mezclada
- ✅ **Después**: Múltiples procesos, responsabilidades claras, escalabilidad independiente

## Requisitos Previos

Antes de levantar el proyecto, asegurate de contar con:
1. **Python 3.10+** instalado en tu maquina.
2. **PostgreSQL** instalado y ejecutandose.
3. **Redis** instalado (para Celery en Fase 4+).
4. El archivo `.env` configurado dentro de la carpeta `backend/`.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                   CLIENTE (Frontend)                        │
│              (HTML/JS/CSS - Fase 7)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   REST API                  WebSocket
(Fase 3)                    (Fase 5)
        │                         │
┌───────▼─────────────────────────▼──────┐
│      DJANGO REST FRAMEWORK             │
│  (API + Autenticación + Lógica)        │
│      (Fases 3, 6)                      │
└─────────┬──────────────────┬───────────┘
          │                  │
          │              ┌───▼──────────────┐
          │              │ Django Channels  │
    ┌─────▼─────┐        │  (WebSocket)     │
    │  Models   │        │  (Fase 5)        │
    │  (Fase 2) │        └──────────────────┘
    └───────────┘
          │
    ┌─────▼──────────────┐
    │   PostgreSQL       │
    │   (Base datos)     │
    └────────────────────┘

┌────────────────────────────────────────┐
│    SERVICIOS DE IA (Encapsulados)      │
│  - PoseModule (YOLO)                   │
│  - BehaviorDetector (LSTM)             │
│  - BehaviorDetector3D                  │
│      (Fase 1)                          │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│    CELERY WORKERS (Tareas Pesadas)     │
│  - Video processing                    │
│  - Pose detection                      │
│  - Behavior analysis                   │
│      (Fase 4)                          │
└─────────────┬──────────────────────────┘
              │
        ┌─────▼──────┐
        │   Redis    │
        │   Broker   │
        └────────────┘
```

## 📅 Fases de Migración

La migración se realiza en **7 fases independientes y validables**:

### Fase 1️⃣: Preparación de Servicios de IA (Semana 1)
**Status**: ✅ Completada  
**Objetivo**: Encapsular modelos de IA sin depender de Flask/Django
**Cambios**: 
- Crear `backend/services/` con módulos independientes
- Copiar `PoseModule.py`, `BehaviorDetector.py`, `BehaviorDetector3d.py` del Tesis
- Crear `config_loader.py` para parámetros
- Validar que funcionen sin frameworks

**Nota de validación**:
- La fase se considera funcional cuando los servicios se importan sin errores y `python test_services.py` termina con `✅ TODOS LOS SERVICIOS DE IA FUNCIONAN CORRECTAMENTE`.
- `backend/services/resources/Conexion.py` es un adaptador legacy para acceso directo a PostgreSQL cuando todavía se necesite SQL crudo.
- En esta etapa no reemplaza a Django ORM; solo sirve como puente temporal para componentes heredados.

**Referencia de cierre**: [backend/FASE_1_COMPLETADA.md](backend/FASE_1_COMPLETADA.md)

### Fase 2️⃣: Modelos Django para Análisis (Semana 1-2)
**Status**: ✅ Completada  
**Objetivo**: Definir BD con Django ORM y registrar los scripts SQL de forma manual
**Cambios**:
- Crear modelos: `VideoUpload`, `DetectionEvent`, `PersonKeypoints`, `AnalysisReport`
- Ejecutar scripts SQL manuales versionados en `backend/scripts/db/update/`
- Validar creación de registros

**Referencia de cierre**: [backend/FASE_2_COMPLETADA.md](backend/FASE_2_COMPLETADA.md)

### Fase 3️⃣: Endpoints REST Básicos (Semana 2)
**Status**: ⏳ Análisis Completado - Implementación en Progreso  
**Objetivo**: Exponer servicios IA a través de REST API y cubrir flujos legacy
**Análisis Realizado**: 
- ✅ 37 endpoints legacy identificados y categorizados en [FASE_3_ESPECIFICACION.md](Doc/FASE_3_ESPECIFICACION.md)
- ✅ Mapeo comparativo legacy→Django en [FASE_3_COMPARATIVA_LEGACY_VS_DJANGO.md](Doc/FASE_3_COMPARATIVA_LEGACY_VS_DJANGO.md)
- ✅ Guía rápida de implementación en [FASE_3_QUICK_START.md](Doc/FASE_3_QUICK_START.md)

**Endpoints Consolidados (9 principales)**:
- **Imágenes**: `POST /api/analysis/images/upload/`, `POST /api/analysis/images/resize/`, `POST /api/analysis/images/save/`
- **Videos**: `POST /api/analysis/videos/upload/`, `POST /api/analysis/videos/{id}/process/`, `GET /api/analysis/videos/{id}/stream/`, `GET /api/analysis/videos/{id}/results/`, `GET /api/analysis/videos/{id}/download/`
- **Frames**: `POST /api/analysis/frames/generate-from-video/`

**Mejoras respecto a Legacy**:
- ✅ Endpoints RESTful (GET/POST/PUT/DELETE) en lugar de POST para todo
- ✅ IDs en lugar de filenames para mejor trazabilidad
- ✅ HTTP 202 Accepted para procesamiento asíncrono
- ✅ SSE (Server-Sent Events) para streaming de progreso
- ✅ Consolidación: 37 endpoints legacy → 9 endpoints principales

**Servicios IA Integrados**:
- YOLO v8s-pose: 17 keypoints COCO format
- LSTM 3-clases: DISTURBIO, NEUTRAL, PELEAR
- BehaviorDetector3D: Análisis 3D opcional

**Nota**: Legacy NO tiene endpoint de entrenamiento; solo inferencia de modelos pre-entrenados.

### Fase 4️⃣: Celery + Redis (Semana 2-3)
**Status**: ⏳ Pendiente  
**Objetivo**: Procesar videos en background
**Cambios**:
- Configurar Celery con Redis broker
- Crear `tasks.py` con tareas asíncronas
- Endpoint para consultar estado `/api/analysis/task-status/{id}/`

### Fase 5️⃣: WebSocket (Semana 3-4)
**Status**: ⏳ Pendiente  
**Objetivo**: Notificaciones en tiempo real
**Cambios**:
- Configurar Django Channels
- Crear `consumers.py` para WebSocket
- Emitir eventos desde Celery tasks

### Fase 6️⃣: Autenticación JWT, Usuarios y Multi-tenant (Semana 4)
**Status**: ✅ Completada  
**Objetivo**: Migrar login, registro y CRUD de usuarios, estableciendo permisos, multi-empresa y asignación de menú de opciones.
**Cambios**:
- Creación de app `authentication` con rutas `/api/auth/` (`login`, `registerAccount`, `verifyCedula`, `verifyEmail`).
- Refactorización de apps `users`, `gestionEmpresas` y `menuOpciones` para un CRUD integral con borrado lógico estricto.
- Soporte Multi-Tenant: Las Instancias soportan múltiples empresas, con roles encapsulados e independientes.
- Autenticación Segura: Generación y validación de tokens JWT nativos protegiendo los endpoints con `IsAuthenticated`.

### Fase 7️⃣: Configuración CORS (Semana 4-5)
**Status**: ⏳ Pendiente  
**Objetivo**: Permitir comunicación frontend-backend sin restricciones CORS
**Cambios**:
- Configurar `django-cors-headers` en `settings.py`
- Permitir orígenes de frontend
- Validar que las llamadas API funcionan desde cliente web
- Mantener seguridad configurando solo orígenes autorizados

**Criterio de éxito**: Frontend puede consumir API sin errores de CORS



---

## 🚀 Pasos para Inicialización (Primera Vez)

Si es la primera vez que clonas o descargas el proyecto, sigue estos pasos para prepararlo en tu entorno local.

### 1. Configurar la Base de Datos

Entra a tu gestor de PostgreSQL (como pgAdmin o DBeaver) y crea la base de datos que vas a utilizar (ej, `DbBioPose`).
Luego, abre un script en esa base de datos y ejecuta la preparacion del esquema multi-ambiente:

```sql
CREATE SCHEMA IF NOT EXISTS "Dev";
GRANT ALL ON SCHEMA "Dev" TO postgres;
```

A continuacion, ejecuta dentro de PostgreSQL el archivo de creacion de tablas maestras ubicado en:
`backend/scripts/db/create/CreateDb.sql`

Este script estructurara la tabla Empresas, Usuarios, Roles, Permisos y Parametros en la base de datos sobre el esquema indicado.

### 2. Configurar Variables de Entorno

Dentro de la carpeta `backend/`, crea un archivo llamado `.env` y ubica dentro los parametros de tu conexion. Por ejemplo:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=DbBioPose
DB_USER=postgres
DB_PASSWORD=tu_contraseña_secreta
DB_SCHEMA=Dev
SECRET_KEY=django-insecure-test-key-please-change-before-production
DEBUG=True
```

### 3. Crear entorno virtual y dependencias

Abre una terminal (PowerShell o CMD) y ejecutalo desde la raiz del `backend`.

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(Nota: Si PowerShell te niega permisos de ejecucion, debes correrlo como administrador y habilitarlos usando `Set-ExecutionPolicy RemoteSigned`)*

Con el entorno activado, instala todas las dependencias requeridas usando el archivo `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### 4. Sincronizar Base de Datos

Luego de crear el esquema, valida y ejecuta manualmente el script SQL correspondiente de la fase. La estructura del esquema debe actualizarse en `backend/scripts/db/create/Esquema BD.sql` para reflejar el estado real del diagrama.
```powershell
# Ejecutar manualmente el script SQL de la fase en PostgreSQL
# luego validar con manage.py check
python manage.py check
```

## Levantar el Servidor de Desarrollo

Una vez hecho todo lo anterior, para arrancar el servidor web solo necesitas correr:

```powershell
# Asegurate de tener el entorno (venv) activo
python manage.py runserver
```

El proyecto iniciara y estaras listo para consumir la nueva API a traves de `http://127.0.0.1:8000/`.

---

## 📁 Estructura de Directorios (Post-Migración)

```
Biopose_BackEnd/
├── backend/
│   ├── manage.py                 # Django CLI
│   ├── .env                      # Variables de entorno (NO subir a git)
│   ├── core/
│   │   ├── settings.py           # Configuración central Django
│   │   ├── urls.py               # Rutas principales
│   │   ├── asgi.py               # Configuración para WebSocket (Fase 5)
│   │   ├── wsgi.py               # Configuración WSGI
│   │   └── celery.py             # Configuración Celery (Fase 4)
│   ├── apps/
│   │   ├── users/
│   │   │   ├── models.py         # Usuarios, roles, permisos (DB schema)
│   │   │   ├── views.py          # Endpoints CRUD de usuarios
│   │   │   ├── serializers.py    # Serialización de datos de entidades
│   │   │   ├── urls.py
│   │   │   └── tests.py
│   │   ├── authentication/
│   │   │   ├── views.py          # Login, registro, verificaciones
│   │   │   ├── serializers.py    # Serializadores auth
│   │   │   ├── urls.py           # Rutas /api/auth/
│   │   │   └── utils.py          # JWT generator y hash_password
│   │   ├── analysis/
│   │   │   ├── models.py         # VideoUpload, DetectionEvent, etc (Fase 2)
│   │   │   ├── views.py          # Endpoints de análisis (Fase 3)
│   │   │   ├── serializers.py    # Serialización de análisis (Fase 3)
│   │   │   ├── tasks.py          # Tareas Celery (Fase 4)
│   │   │   ├── consumers.py      # WebSocket consumers (Fase 5)
│   │   │   ├── routing.py        # Rutas WebSocket (Fase 5)
│   │   │   ├── urls.py
│   │   │   └── tests.py
│   ├── services/                 # Capa de servicios de IA (Fase 1)
│   │   ├── __init__.py
│   │   ├── pose_detection.py
│   │   ├── behavior_detection.py
│   │   ├── behavior_3d_detection.py
│   │   ├── video_processor.py
│   │   ├── config_loader.py
│   │   ├── models/               # Copias de modelos del Tesis
│   │   └── resources/            # Copias de resources del Tesis
│   ├── scripts/
│   │   └── db/
│   │       ├── create/           # Scripts iniciales
│   │       ├── update/           # Scripts incrementales
│   │       ├── fix/              # Scripts de corrección
│   │       └── data/             # Datos semilla
│   ├── resources/
│   │   ├── datasets/
│   │   ├── models/               # Pesos YOLO, LSTM
│   │   ├── test_videos/
│   │   └── training_videos/
│   ├── media/                    # Archivos generados + uploads (Fase 3+)
│   │   ├── images/
│   │   │   ├── uploads/          # Imágenes subidas por usuario
│   │   │   └── processed/        # Imágenes procesadas con YOLO
│   │   └── videos/
│   │       ├── uploads/          # Videos subidos sin procesar
│   │       ├── processing/       # Videos en procesamiento
│   │       └── results/          # Videos procesados con LSTM
│   └── static/                   # Recursos estáticos (CSS, JS frontend)
│       └── ...
├── frontend/                      # (Opcional) Frontend consumidor separado
│   ├── index.html                 # Cliente web que consume API
│   ├── js/
│   │   ├── api-client.js         # Cliente REST API
│   │   ├── websocket-client.js   # Cliente WebSocket
│   │   └── ui.js
│   ├── css/
│   └── assets/
├── Doc/
│   ├── PLAN_MIGRACION.md    # Plan detallado (todas las fases)
│   ├── FASE_3_ESPECIFICACION.md             # Especificación endpoints Fase 3
│   ├── FASE_3_COMPARATIVA_LEGACY_VS_DJANGO.md # Mapeo Flask → Django
│   ├── FASE_3_QUICK_START.md                # Guía rápida de inicio
│   ├── MIGRACION_ARQUITECTURA.md            # Arquitectura objetivo
│   ├── ESPECIFICACION_DESARROLLO.md         # Reglas y principios SOLID
│   └── Glosario_Desarrollo.md               # Términos técnicos
├── README.md
├── yolov8s-pose.pt
└── .gitignore

```

**Cambios en Estructura de Archivos (Fase 3)**:
- ✅ Nuevo directorio `backend/media/` para uploads y archivos generados
- ✅ Subdirectorios por tipo: `images/`, `videos/`
- ✅ Estados de procesamiento: `uploads/`, `processing/`, `results/`
- ✅ Legacy usaba `Tesis/src/static/videos/`. Ahora centralizado en `backend/media/`


## 🔄 Guía por Fases de Desarrollo

### Fase 1
La capa de servicios de IA ya quedó encapsulada e independiente. El cierre oficial está en [backend/FASE_1_COMPLETADA.md](backend/FASE_1_COMPLETADA.md).

### Fase 2
Los modelos Django y el DDL manual ya quedaron definidos. El cierre oficial está en [backend/FASE_2_COMPLETADA.md](backend/FASE_2_COMPLETADA.md).

### Siguiente Paso
Continuar con Fase 3 usando el plan detallado en [Doc/PLAN_MIGRACION.md](./Doc/PLAN_MIGRACION.md).

---

## 🐛 Solución de Problemas

### "ModuleNotFoundError: No module named 'django'"
Asegurate de haber activado el entorno virtual:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip list  # Verifica que django esté instalado
```

### "psycopg2 connection error"
Verifica que PostgreSQL esté ejecutándose y que las credenciales en `.env` sean correctas.

### "Redis connection error" (Fase 4+)
Asegurate de tener Redis instalado y ejecutándose:
```powershell
redis-server  # En Windows, instala desde: https://github.com/microsoftarchive/redis/releases
```

---

## 📊 Estado Actual del Proyecto

| Componente | Estado | Fase |
|-----------|--------|------|
| Estructura Django base | ✅ Listo | - |
| Servicios de IA | ✅ Completado | 1 |
| Modelos Django | ✅ Completado | 2 |
| API REST | ⏳ En Progreso (Swagger OK) | 3 |
| Celery + Redis | ⏳ Pendiente | 4 |
| WebSocket | ⏳ Pendiente | 5 |
| Autenticación Auth/Users | ✅ Completado | 6 |
| Configuración CORS | ⏳ Pendiente | 7 |

---

## 📝 Notas Importantes

- **El código del Tesis se mantiene intacto** durante la migración para permitir rollback
- **Cada fase es independiente** y se puede validar antes de continuar
- **El README se actualiza** conforme avanza cada fase
- **Documentación es viva**: Los archivos en `Doc/` se actualizan con cambios arquitectónicos

---

## 🤝 Contribuciones

Cuando trabajes en una fase:
1. Lee el plan de esa fase en [PLAN_MIGRACION.md](./Doc/PLAN_MIGRACION.md)
2. Sigue las [ESPECIFICACION_DESARROLLO.md](./Doc/ESPECIFICACION_DESARROLLO.md)
3. Actualiza este README cuando completes una fase
4. Documenta cambios en los archivos de `Doc/`