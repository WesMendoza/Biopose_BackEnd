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
│                   CLIENTE (Frontend)                         │
│              (HTML/JS/CSS - Fase 7)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   REST API                  WebSocket
(Fase 3)                    (Fase 5)
        │                         │
┌───────▼─────────────────────────▼──────┐
│      DJANGO REST FRAMEWORK              │
│  (API + Autenticación + Lógica)        │
│      (Fases 3, 6)                       │
└─────────┬──────────────────┬────────────┘
          │                  │
          │              ┌───▼──────────────┐
          │              │ Django Channels  │
    ┌─────▼─────┐       │  (WebSocket)    │
    │  Models   │       │  (Fase 5)        │
    │  (Fase 2) │       └────────────────────┘
    └───────────┘
          │
    ┌─────▼──────────────┐
    │   PostgreSQL       │
    │   (Base datos)     │
    └────────────────────┘

┌────────────────────────────────────────┐
│    SERVICIOS DE IA (Encapsulados)      │
│  - PoseModule (YOLO)                  │
│  - BehaviorDetector (LSTM)            │
│  - BehaviorDetector3D                 │
│      (Fase 1)                          │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│    CELERY WORKERS (Tareas Pesadas)    │
│  - Video processing                   │
│  - Pose detection                     │
│  - Behavior analysis                  │
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
**Status**: ⏳ Pendiente  
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

### Fase 2️⃣: Modelos Django para Análisis (Semana 1-2)
**Status**: ⏳ Pendiente  
**Objetivo**: Definir BD con Django ORM
**Cambios**:
- Crear modelos: `VideoUpload`, `DetectionEvent`, `PersonKeypoints`, `AnalysisReport`
- Ejecutar migraciones Django
- Validar creación de registros

### Fase 3️⃣: Endpoints REST Básicos (Semana 2)
**Status**: ⏳ Pendiente  
**Objetivo**: Exponer servicios a través de API
**Cambios**:
- Crear `serializers.py` y `views.py` en `apps/analysis`
- Endpoints: `/api/analysis/upload-video/`, `/api/analysis/detect-pose/`, etc.
- Validar con Postman/cURL

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

### Fase 6️⃣: Autenticación JWT (Semana 4)
**Status**: ⏳ Pendiente  
**Objetivo**: Migrar login del Flask a Django
**Cambios**:
- Endpoint `/api/users/login/`
- JWT tokens
- Proteger endpoints con permisos

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

Con el entorno activado, instala todas las dependencias requeridas del backend:
```powershell
pip install django djangorestframework channels celery redis psycopg2-binary python-dotenv
```

### 4. Sincronizar Base de Datos

Luego de crear el esquema, aplica las migraciones internas de Django:
```powershell
python manage.py migrate
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
│   │   │   ├── models.py         # Usuarios, roles, permisos
│   │   │   ├── views.py          # Endpoints de usuarios
│   │   │   ├── serializers.py    # Serialización de datos
│   │   │   ├── urls.py
│   │   │   └── tests.py
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
│   └── static/
│       └── videos/
│           ├── live/
│           └── uploads/
├── frontend/                      # (Opcional) Frontend consumidor separado
│   ├── index.html                 # Cliente web que consume API
│   ├── js/
│   │   ├── api-client.js         # Cliente REST API
│   │   ├── websocket-client.js   # Cliente WebSocket
│   │   └── ui.js
│   ├── css/
│   └── assets/
├── Doc/
│   ├── PLAN_MIGRACION_INCREMENTALV2.md    # Plan detallado (todas las fases)
│   ├── MIGRACION_ARQUITECTURA.md           # Arquitectura objetivo
│   └── ESPECIFICACION_DESARROLLO.md        # Reglas y principios SOLID
├── Tesis/                        # Código legacy (será deprecado)
│   ├── src/
│   │   ├── main.py               # Monolito Flask original
│   │   ├── model/                # Modelos IA (PoseModule, BehaviorDetector, etc)
│   │   ├── models/               # Pesos entrenados (LSTM)
│   │   ├── Resources/            # Utilidades (Encrypt, Helper, etc)
│   │   └── ...
│   └── ...
└── README.md                      # Este archivo
```

---

## 🔄 Guía por Fases de Desarrollo

### ✅ AHORA: Fase 1 (Preparación de Servicios de IA)

Esta es la fase que iniciamos inmediatamente. El objetivo es crear una capa de servicios encapsulada que funcione independientemente de Django/Flask.

#### Paso 1: Crear estructura de directorios
```powershell
cd backend
mkdir services
mkdir services\models
mkdir services\resources
# Crear archivos __init__.py en cada carpeta
```

#### Paso 2: Copiar módulos del Tesis
Vamos a extraer los servicios del monolito Flask y colocarlos en el directorio de servicios:

```
De Tesis/src/model/                → a backend/services/models/
├── PoseModule.py                  → PoseModule.py
├── BehaviorDetector.py            → BehaviorDetector.py
└── BehaviorDetector3d.py          → BehaviorDetector3d.py

De Tesis/src/Resources/            → a backend/services/resources/
├── Encrypt.py                     → Encrypt.py
├── Helper.py                      → Helper.py
├── Middleware.py                  → Middleware.py
├── Conexion.py                    → Conexion.py (adaptar para no usar Flask)
└── ...                            → ...
```

#### Paso 3: Crear servicios envolventes
Crear archivos que encapsulen la lógica de IA sin dependencias de frameworks:

```python
# backend/services/pose_detection.py
"""
Servicio de detección de pose independiente de Django/Flask.
Encapsula PoseModule para reutilización en diferentes contextos.
"""
from services.models.PoseModule import PoseModule
import os

class PoseDetectionService:
    """Servicio de detección de postura humana usando YOLO."""
    
    def __init__(self, model_path: str = None):
        """
        Inicializa el servicio con el modelo YOLO.
        
        Args:
            model_path: Ruta al archivo del modelo YOLO (ej: yolov8s-pose.pt)
        """
        if model_path is None:
            model_path = os.getenv('POSE_MODEL_PATH', 'yolov8s-pose.pt')
        
        self.pose_module = PoseModule(model_path)
    
    def detect_pose_from_image(self, image_path: str):
        """Detectar pose en una imagen."""
        return self.pose_module.detect(image_path)
    
    def detect_pose_from_frame(self, frame):
        """Detectar pose en un frame de video (numpy array)."""
        return self.pose_module.detect_frame(frame)
```

```python
# backend/services/behavior_detection.py
"""Servicio de detección de comportamiento usando LSTM."""
from services.models.BehaviorDetector import BehaviorDetector
import os

class BehaviorDetectionService:
    """Servicio de detección de comportamiento (pelea, disturbio, etc)."""
    
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.getenv('BEHAVIOR_MODEL_PATH', 'lstm_model.pt')
        
        self.behavior_detector = BehaviorDetector(model_path)
    
    def analyze_keypoints(self, keypoints_sequence):
        """Analizar secuencia de keypoints y clasificar comportamiento."""
        return self.behavior_detector.classify(keypoints_sequence)
```

```python
# backend/services/config_loader.py
"""
Cargador de configuración centralizado.
Define parámetros del sistema (thresholds, tamaños, etc).
"""
import os
from dotenv import load_dotenv

load_dotenv()

class AIConfig:
    """Configuración de modelos de IA."""
    
    # Rutas de modelos
    POSE_MODEL_PATH = os.getenv('POSE_MODEL_PATH', 'yolov8s-pose.pt')
    BEHAVIOR_MODEL_PATH = os.getenv('BEHAVIOR_MODEL_PATH', 'lstm_model.pt')
    BEHAVIOR_3D_MODEL_PATH = os.getenv('BEHAVIOR_3D_MODEL_PATH', 'lstm_3d_model.pt')
    
    # Parámetros de detección
    POSE_CONFIDENCE_THRESHOLD = float(os.getenv('POSE_CONFIDENCE', 0.5))
    BEHAVIOR_CONFIDENCE_THRESHOLD = float(os.getenv('BEHAVIOR_CONFIDENCE', 0.7))
    
    # Parámetros de video
    VIDEO_FRAME_SKIP = int(os.getenv('FRAME_SKIP', 2))
    SEQUENCE_LENGTH = int(os.getenv('SEQUENCE_LENGTH', 30))
    
    @classmethod
    def to_dict(cls):
        """Retorna configuración como diccionario."""
        return {
            'pose_model': cls.POSE_MODEL_PATH,
            'behavior_model': cls.BEHAVIOR_MODEL_PATH,
            'pose_threshold': cls.POSE_CONFIDENCE_THRESHOLD,
            'behavior_threshold': cls.BEHAVIOR_CONFIDENCE_THRESHOLD,
        }
```

#### Paso 4: Validar independencia
Verificar que los servicios funcionan **sin Django ni Flask**:

```powershell
# Activar venv
cd backend
.\venv\Scripts\Activate.ps1

# Probar importación de servicios
python -c "from services.pose_detection import PoseDetectionService; print('✓ PoseDetectionService importado correctamente')"

python -c "from services.behavior_detection import BehaviorDetectionService; print('✓ BehaviorDetectionService importado correctamente')"

python -c "from services.config_loader import AIConfig; print('✓ Configuración cargada:', AIConfig.to_dict())"
```

#### Paso 5: Crear script de prueba simple
Crear archivo `test_services.py` en la raíz de `backend/`:

```python
#!/usr/bin/env python
"""Script de prueba para validar servicios de IA en Fase 1."""

from services.pose_detection import PoseDetectionService
from services.behavior_detection import BehaviorDetectionService
from services.config_loader import AIConfig

def test_pose_service():
    """Prueba servicio de pose."""
    print("🔍 Probando servicio de detección de pose...")
    service = PoseDetectionService()
    print(f"✓ Servicio inicializado con modelo: {AIConfig.POSE_MODEL_PATH}")
    # Aquí irían pruebas con imágenes reales
    print("✓ Servicio de pose listo para usar")

def test_behavior_service():
    """Prueba servicio de comportamiento."""
    print("\n🔍 Probando servicio de detección de comportamiento...")
    service = BehaviorDetectionService()
    print(f"✓ Servicio inicializado con modelo: {AIConfig.BEHAVIOR_MODEL_PATH}")
    # Aquí irían pruebas con secuencias reales
    print("✓ Servicio de comportamiento listo para usar")

def test_config():
    """Prueba carga de configuración."""
    print("\n⚙️  Configuración del Sistema:")
    for key, value in AIConfig.to_dict().items():
        print(f"  - {key}: {value}")

if __name__ == '__main__':
    print("=" * 60)
    print("VALIDACIÓN FASE 1: SERVICIOS DE IA")
    print("=" * 60)
    
    try:
        test_config()
        test_pose_service()
        test_behavior_service()
        print("\n" + "=" * 60)
        print("✅ TODOS LOS SERVICIOS FUNCIONAN CORRECTAMENTE")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
```

Ejecutar test:
```powershell
python test_services.py
```

#### Criterio de Éxito de Fase 1:
- ✅ Los 3 directorios (`models/`, `resources/`, `.py`) existen en `backend/services/`
- ✅ Los servicios se importan sin errores
- ✅ `AIConfig` carga correctamente desde `.env`
- ✅ No hay dependencias de Django o Flask en los servicios
- ✅ El script de prueba `test_services.py` ejecuta sin errores

---

## ⚙️ Próximos Pasos (Fase 2)

Una vez que Fase 1 esté completa:
1. Definir modelos Django en `apps/analysis/models.py`
2. Ejecutar `python manage.py makemigrations`
3. Ejecutar `python manage.py migrate`
4. Validar creación de tablas en PostgreSQL

---

## 📚 Documentación Adicional

- [Plan de Migración Detallado](./Doc/PLAN_MIGRACION_INCREMENTALV2.md) - Todas las fases y tareas
- [Arquitectura Objetivo](./Doc/MIGRACION_ARQUITECTURA.md) - Explicación del cambio de arquitectura
- [Especificaciones de Desarrollo](./Doc/ESPECIFICACION_DESARROLLO.md) - Normas y principios SOLID
- [Glosario de Términos](./Doc/Glosario_Desarrollo.md) - Definiciones técnicas claras y mantenibles

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
| Servicios de IA | ⏳ Pendiente | 1 |
| Modelos Django | ⏳ Pendiente | 2 |
| API REST | ⏳ Pendiente | 3 |
| Celery + Redis | ⏳ Pendiente | 4 |
| WebSocket | ⏳ Pendiente | 5 |
| Autenticación JWT | ⏳ Pendiente | 6 |
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
1. Lee el plan de esa fase en [PLAN_MIGRACION_INCREMENTALV2.md](./Doc/PLAN_MIGRACION_INCREMENTALV2.md)
2. Sigue las [ESPECIFICACION_DESARROLLO.md](./Doc/ESPECIFICACION_DESARROLLO.md)
3. Actualiza este README cuando completes una fase
4. Documenta cambios en los archivos de `Doc/`