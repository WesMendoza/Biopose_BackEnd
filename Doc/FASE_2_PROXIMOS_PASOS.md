# 🚀 PRÓXIMOS PASOS: TRANSICIÓN A FASE 2

## Estado Actual

- ✅ **Fase 1 Completada**: Servicios de IA encapsulados e independientes
- ⏳ **Siguiente**: Fase 2 - Modelos Django para Análisis

---

## Fase 2: Crear Modelos Django para Análisis

### Objetivo
Definir la estructura de datos en Django usando ORM, sin necesidad de SQL raw.

### Decisiones de diseño (explícitas)

Para evitar ambigüedades antes de ejecutar el DDL, se registran las decisiones de diseño que guiarán la implementación y validación de Fase 2:

- Alcance de auditoría: todos los uploads y reportes deberán registrar `idUsuario` (quien sube/procesa) y **también** `idEmpresa` cuando aplique (para permitir agregados por tenant). Esto implica añadir `idEmpresa` como FK en `analysis_videoupload` y `analysis_report` si el entorno es multi-empresa.
- Parámetros de aplicación: No duplicar fuentes de verdad. Recomendación:
    - Usar `parametrosCabecera` / `parametroDetalle` como fuente de configuración por empresa/cliente (scope por `idEmpresa`).
    - Mantener `systemParameter` únicamente para parámetros globales de la aplicación (flags operativos, umbrales por defecto).
    - Definir una resolución de parámetros (fallback): buscar `parametro` con `idEmpresa` → si no existe, usar `systemParameter` global.
- Almacenamiento de keypoints:
    - `analysis_personkeypoints` puede permanecer en la BD si el volumen es moderado y se requiere reproducción forense rápida.
    - Si el volumen esperado es grande, guardar keypoints en objeto (S3/Blob) o ficheros Parquet y almacenar sólo metadatos/URI en la tabla; mantener índices en `detectionevent` para navegación.
- Indexación y búsquedas en JSON:
    - Campos JSON (`detalles`, `estadisticas`, `resumenJson`) deben usar `JSONB` y `GIN` indexes cuando se requieran consultas por claves/valores.
    - Para filtros frecuentes, añadir columnas derivadas (e.g., `confidence_avg`, `has_fight boolean`) para acelerar consultas.
- Volumen y partitioning:
    - Evaluar particionado por fecha o `idEmpresa` si el volumen crece. Definir políticas de retención/archivado para keypoints y eventos antiguos.
- Scripts y control de cambios DB:
    - Todas las alteraciones a esquemas deben ir a `backend/scripts/db/update/` y documentarse en `FASE_2_COMPLETADA.md`.
    - No usar `makemigrations` para estas tablas si la política del proyecto exige SQL versionado manualmente.

Estas decisiones se aplicarán al preparar el DDL (`001_fase2_analysis_tables.sql`) y al mapping en `apps/analysis/models.py` (manteniendo `managed=False` hasta que el script se ejecute en DB).

### Tiempo Estimado
1-2 semanas

### Tareas

#### Tarea 1: Definir Modelos Django

**Archivo**: `backend/apps/analysis/models.py`

Agregar 4 modelos principales:

```python
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class VideoUpload(models.Model):
    """Información del video subido por el usuario."""
    
    PROCESSING_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='videos/uploads/%Y/%m/%d/')
    duration_seconds = models.IntegerField(null=True, blank=True)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PROCESSING_CHOICES, default='pending')
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.status})"
    
    class Meta:
        ordering = ['-uploaded_at']
        db_table = 'analysis_videoupload'


class DetectionEvent(models.Model):
    """Evento de comportamiento detectado."""
    
    BEHAVIOR_CHOICES = [
        ('pelea', 'Pelea'),
        ('disturbio', 'Disturbio'),
        ('normal', 'Comportamiento Normal'),
    ]
    
    video = models.ForeignKey(VideoUpload, on_delete=models.CASCADE, related_name='events')
    behavior_type = models.CharField(max_length=20, choices=BEHAVIOR_CHOICES)
    confidence = models.FloatField()  # 0.0 a 1.0
    
    start_frame = models.IntegerField()
    end_frame = models.IntegerField()
    timestamp_start = models.FloatField()  # segundos desde inicio del video
    timestamp_end = models.FloatField()
    
    detected_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.behavior_type} @ {self.timestamp_start}s"
    
    class Meta:
        ordering = ['timestamp_start']
        db_table = 'analysis_detectionevent'
        indexes = [
            models.Index(fields=['video', 'detected_at']),
        ]


class PersonKeypoints(models.Model):
    """Puntos clave detectados de una persona en un frame."""
    
    event = models.ForeignKey(DetectionEvent, on_delete=models.CASCADE, related_name='keypoints')
    person_id = models.IntegerField()  # ID de la persona en el video
    frame_number = models.IntegerField()
    
    # Almacenar keypoints como JSON
    # Estructura: {"0": {"x": 0.5, "y": 0.3, "z": 0.2, "confidence": 0.98}, ...}
    keypoints_json = models.JSONField(default=dict)
    
    detected_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Person {self.person_id} @ Frame {self.frame_number}"
    
    class Meta:
        db_table = 'analysis_personkeypoints'
        indexes = [
            models.Index(fields=['event', 'person_id']),
        ]


class AnalysisReport(models.Model):
    """Reporte consolidado de análisis."""
    
    video = models.OneToOneField(VideoUpload, on_delete=models.CASCADE, related_name='report')
    
    total_frames = models.IntegerField()
    total_duration_seconds = models.FloatField()
    
    # Contadores
    events_count = models.IntegerField(default=0)
    pelea_count = models.IntegerField(default=0)
    disturbio_count = models.IntegerField(default=0)
    
    # Estadísticas
    avg_confidence = models.FloatField(default=0.0)
    max_confidence = models.FloatField(default=0.0)
    
    # Metadata
    processed_by = models.CharField(max_length=50, default='celery-worker')
    processing_time_seconds = models.FloatField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Report: {self.video.title}"
    
    class Meta:
        db_table = 'analysis_analysisreport'
```

---

#### Tarea 2: Aplicar Script SQL Manual (DDL)

```bash
# Ejecutar en PostgreSQL (esquema Dev)
backend/scripts/db/update/001_fase2_analysis_tables.sql
```

**Resultado esperado**:
```
CREATE TABLE
CREATE INDEX
CREATE TRIGGER
```

Nota: El script `001_fase2_analysis_tables.sql` incluye la columna `idEmpresa` (FK a `empresa`) y campos de auditoría (`usuarioCreacion`, `fechaCreacion`, `usuarioModificacion`, `fechaModificacion`) en las tablas relevantes. Esto permite agregados por tenant y trazabilidad por usuario.

---

#### Tarea 3: Validar en Base de Datos

```sql
-- PostgreSQL
\dt analysis_*;  -- Listar tablas

SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'Dev' 
AND table_name LIKE 'analysis_%';
```

**Tablas esperadas**:
```
- analysis_videoupload
- analysis_detectionevent
- analysis_personkeypoints
- analysis_analysisreport
```

---

#### Tarea 4: Registrar en Admin (Django Admin)

**Archivo**: `backend/apps/analysis/admin.py`

```python
from django.contrib import admin
from .models import VideoUpload, DetectionEvent, PersonKeypoints, AnalysisReport

@admin.register(VideoUpload)
class VideoUploadAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'uploaded_at', 'file_size_mb']
    list_filter = ['status', 'uploaded_at']
    search_fields = ['title']
    readonly_fields = ['uploaded_at', 'processed_at']

@admin.register(DetectionEvent)
class DetectionEventAdmin(admin.ModelAdmin):
    list_display = ['behavior_type', 'confidence', 'timestamp_start', 'detected_at']
    list_filter = ['behavior_type', 'detected_at']
    search_fields = ['video__title']

@admin.register(PersonKeypoints)
class PersonKeypointsAdmin(admin.ModelAdmin):
    list_display = ['person_id', 'frame_number', 'detected_at']
    list_filter = ['detected_at']

@admin.register(AnalysisReport)
class AnalysisReportAdmin(admin.ModelAdmin):
    list_display = ['video', 'events_count', 'avg_confidence', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
```

---

### Checklist de Fase 2

- [ ] 1. Definir los 4 modelos en `apps/analysis/models.py`
- [ ] 2. Crear script DDL en `backend/scripts/db/update/`
- [ ] 3. Ejecutar script en PostgreSQL (esquema `Dev`)
- [ ] 4. Validar tablas en PostgreSQL
- [ ] 5. Registrar modelos en `apps/analysis/admin.py`
- [ ] 6. Probar creación de registros via Django shell:
  ```bash
  python manage.py shell
  >>> from apps.analysis.models import VideoUpload
    >>> VideoUpload.objects.create(nombreOriginal="test.mp4", rutaArchivo="/tmp/test.mp4", tamanioBytes=1024)
  ```
- [ ] 7. Crear documento `FASE_2_COMPLETADA.md`

---

### Criterio de Éxito de Fase 2

- ✅ 4 modelos definidos sin errores
- ✅ Scripts SQL versionados y ejecutados correctamente
- ✅ Tablas creadas en PostgreSQL
- ✅ Registros creables en Django shell
- ✅ Admin de Django funcional

---

## Comandos Clave

```bash
# Activar venv
cd backend
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Validar que el proyecto Django carga correctamente
python manage.py check

# Django shell para pruebas
python manage.py shell

# Verificar tablas de analysis en PostgreSQL
# SELECT table_name FROM information_schema.tables
# WHERE table_schema = 'Dev' AND table_name LIKE 'analysis_%';

# Crear superusuario si no existe
python manage.py createsuperuser
```

---

## Archivos a Modificar/Crear

| Archivo | Acción | Importancia |
|---------|--------|-------------|
| `apps/analysis/models.py` | Modificar | ⭐⭐⭐ CRÍTICO |
| `apps/analysis/admin.py` | Modificar | ⭐⭐ Alta |
| `scripts/db/update/*.sql` | Crear/Versionar DDL | ⭐⭐⭐ CRÍTICO |
| `.env` | Verificar | ⭐ Media |

---

## Dependencias para Fase 2

✅ Ya completadas:
- `Django` - Instalado
- `psycopg2-binary` - Instalado
- `python-dotenv` - Instalado

---

## Diagrama de Flujo (Fase 1 → Fase 2 → Fase 3)

```
Fase 1: Servicios IA ✅
    └─ PoseDetectionService
    └─ BehaviorDetectionService
    └─ SystemConfig

           ↓↓↓

Fase 2: Modelos Django ⏳
    └─ VideoUpload
    └─ DetectionEvent
    └─ PersonKeypoints
    └─ AnalysisReport

           ↓↓↓

Fase 3: API REST (Próximo)
    └─ Serializers
    └─ ViewSets
    └─ Endpoints: /api/analysis/*
```

---

## Dudas Comunes

### ¿Por qué usamos models.JSONField()?
Para almacenar keypoints complejos sin normalizar toda la estructura. Permite flexibilidad y búsquedas posteriores con queries.

### ¿Por qué ForeignKey y no OneTOOne?
`VideoUpload → DetectionEvent`: 1 video puede tener múltiples eventos (OneToMany)  
`DetectionEvent → PersonKeypoints`: 1 evento puede tener múltiples personas (OneToMany)

### ¿Cuándo ejecutar cambios de base de datos?
Después de cada ajuste de estructura en `models.py` y siempre por scripts SQL versionados:
1. Crear script en `backend/scripts/db/update/`
2. Ejecutar script en PostgreSQL (entorno Dev)
3. Validar tablas/columnas/índices

---

## Próximos Hitos

| Fase | Estado | Estimado |
|------|--------|----------|
| Fase 1 | ✅ COMPLETADA | - |
| Fase 2 | ⏳ EN PROGRESO | 1-2 semanas |
| Fase 3 | ⏳ Próxima | 1 semana |
| Fase 4 | ⏳ Después | 1-2 semanas |

---

**Documentación**: Consultar [PLAN_MIGRACION_INCREMENTALV2.md](PLAN_MIGRACION_INCREMENTALV2.md) para detalles completos

**Soporte**: Ver [ESPECIFICACION_DESARROLLO.md](ESPECIFICACION_DESARROLLO.md) para principios SOLID y mejores prácticas
