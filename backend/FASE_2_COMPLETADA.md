# ✅ FASE 2: Modelos Django para Análisis - COMPLETADA

## Resumen de Ejecución

**Fecha Inicio**: [COMPLETAR]  
**Fecha Finalización**: [COMPLETAR]  
**Responsable**: [COMPLETAR]  
**Estado**: 🔄 EN PROGRESO / ✅ COMPLETADA / ❌ PENDIENTE

---

## 1. Modelos Django

### Estado: ✅ COMPLETADO

**Archivos**:
- ✅ `backend/apps/analysis/models.py` - 5 modelos definidos
  - `VideoUpload` - Metadatos de videos
  - `DetectionEvent` - Eventos detectados
  - `PersonKeypoints` - Keypoints por persona/frame
  - `AnalysisReport` - Reporte consolidado
  - `SystemParameter` - Parámetros globales

**Validación Django**:
```bash
python manage.py check
# Resultado esperado: "System check identified no issues (0 silenced)."
```

**Resultado**:
```
[COMPLETAR CON SALIDA REAL]
```

---

## 2. Script SQL - Ejecución Manual

### Archivo: `backend/scripts/db/update/001_fase2_analysis_tables.sql`

**Cambios Incluidos**:
- ✅ Tabla `analysis_videoupload` (con idEmpresa, campos de auditoría)
- ✅ Tabla `analysis_detectionevent` (con campos de auditoría)
- ✅ Tabla `analysis_personkeypoints` (con campos de auditoría)
- ✅ Tabla `analysis_report` (con idEmpresa, campos de auditoría)
- ✅ Tabla `systemParameter` (global)
- ✅ Índices en todas las tablas
- ✅ Trigger `fn_set_actualizadoen_analysis_report` para mantener timestamps

### Ejecución Manual

**Paso 1: Validar Script**
```bash
# Revisar el contenido del script antes de ejecutar
cat backend/scripts/db/update/001_fase2_analysis_tables.sql

# Puntos a validar:
# ✓ SET search_path TO "Dev"; está al inicio
# ✓ Todas las tablas tienen managed=False en Django
# ✓ FKs correctas (idEmpresa a empresa, idUsuario a users)
# ✓ Índices nombrados consistentemente
```

**Resultado de Validación**:
```
[COMPLETAR: Describir qué se verificó]
```

**Paso 2: Ejecutar en PostgreSQL**

Opción A - Usando psql (recomendado):
```bash
psql -U postgres -d DbBioPose -f backend/scripts/db/update/001_fase2_analysis_tables.sql
```

Opción B - Usando herramienta gráfica (DBeaver, pgAdmin):
1. Conectar a esquema "Dev"
2. Abrir archivo SQL
3. Ejecutar (F5 o botón Execute)

**Resultado de Ejecución**:
```
[COMPLETAR CON SALIDA]
Ejemplo esperado:
CREATE TABLE
CREATE INDEX
CREATE TRIGGER
(sin errores)
```

---

## 3. Validación en Base de Datos

### Paso 3: Verificar Tablas Creadas

```sql
-- Ejecutar en PostgreSQL
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'Dev'
  AND table_name IN (
    'analysis_videoupload',
    'analysis_detectionevent',
    'analysis_personkeypoints',
    'analysis_report',
    'systemParameter'
  )
ORDER BY table_name;
```

**Resultado Esperado**:
```
        table_name
─────────────────────────────────
 analysis_detectionevent
 analysis_personkeypoints
 analysis_report
 analysis_videoupload
 systemParameter
(5 filas)
```

**Resultado Real**:
```
[COMPLETAR]
```

### Paso 4: Verificar Campos de Auditoría

```sql
-- Verificar analysis_videoupload
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'Dev' AND table_name = 'analysis_videoupload'
ORDER BY ordinal_position;

-- Resultado esperado:
-- idVideoUpload, idUsuario, idEmpresa, nombreOriginal, rutaArchivo,
-- tamanioBytes, duracionSegundos, fps, estado, celeryTaskId,
-- fechaCarga, fechaProcesamiento
```

**Resultado Real**:
```
[COMPLETAR]
```

### Paso 5: Verificar Índices

```sql
-- Ver índices creados
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'Dev'
  AND tablename LIKE 'analysis_%'
ORDER BY tablename, indexname;
```

**Resultado Esperado**:
```
[Listar índices]
- ix_video_estado
- ix_video_fechacarga
- ix_event_video_fecha
- ix_event_tipo
- ix_kp_event_person
- ix_kp_frame
```

**Resultado Real**:
```
[COMPLETAR]
```

---

## 4. Actualizar Esquema BD

### Paso 6: Actualizar `Esquema BD.sql`

**Acción**: Modificar `backend/scripts/db/create/Esquema BD.sql` para reflejar las nuevas tablas.

**Ubicación**: Agregar después de las tablas maestras y antes de comentarios finales:

```dbml
TABLE analysis_videoupload {
  idVideoUpload int [primary key]
  idUsuario int [ref: > users.idUsuario]
  idEmpresa int [ref: > empresa.idEmpresa]
  nombreOriginal varchar
  rutaArchivo varchar
  tamanioBytes bigint
  duracionSegundos float
  fps float
  estado varchar
  celeryTaskId varchar
  fechaCarga datetime
  fechaProcesamiento datetime
}

TABLE analysis_detectionevent {
  idDetectionEvent int [primary key]
  idVideoUpload int [ref: > analysis_videoupload.idVideoUpload]
  tipoEvento varchar
  confianza float
  frameInicio int
  frameFin int
  tiempoInicio float
  tiempoFin float
  personasInvolucradas int
  detalles json
  fechaCreacion datetime
  usuarioCreacion varchar
  usuarioModificacion varchar
  fechaModificacion datetime
}

TABLE analysis_personkeypoints {
  idPersonKeypoints int [primary key]
  idDetectionEvent int [ref: > analysis_detectionevent.idDetectionEvent]
  personId int
  frameNumber int
  keypointsJson json
  fechaCreacion datetime
  usuarioCreacion varchar
  usuarioModificacion varchar
  fechaModificacion datetime
}

TABLE analysis_report {
  idAnalysisReport int [primary key]
  idVideoUpload int [unique, ref: > analysis_videoupload.idVideoUpload]
  idEmpresa int [ref: > empresa.idEmpresa]
  totalFrames int
  totalDuracionSegundos float
  totalEventos int
  totalPeleas int
  totalDisturbios int
  confianzaPromedio float
  confianzaMaxima float
  tiempoProcesamientoSegundos float
  estadisticas json
  resumenJson json
  generadoEn datetime
  actualizadoEn datetime
  usuarioCreacion varchar
  usuarioModificacion varchar
  fechaCreacion datetime
  fechaModificacion datetime
}

TABLE systemParameter {
  idParameter int [primary key]
  codigo varchar [unique]
  valor varchar
  descripcion varchar
  tipo varchar
}
```

**Validación**: ¿Se actualizó correctamente?
- [ ] Sí, `Esquema BD.sql` refleja las nuevas tablas
- [ ] No, requiere revisión

---

## 5. Validación en Django Shell

### Paso 7: Probar Modelos en Django

```bash
cd backend
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

python manage.py shell
```

```python
# Dentro del shell Django
from apps.analysis.models import VideoUpload, DetectionEvent, SystemParameter

# Verificar que la tabla existe
print(VideoUpload.objects.all())
# Resultado esperado: <QuerySet []> (tabla vacía, sin errores)

# Intentar crear un registro dummy (sin usuario/empresa reales)
v = VideoUpload(
    nombreOriginal="test.mp4",
    rutaArchivo="/tmp/test.mp4",
    tamanioBytes=1024,
    estado="PENDING"
)
v.save()
print(f"✓ VideoUpload creado: {v}")

# Verificar que puede ser recuperado
retrieved = VideoUpload.objects.get(pk=v.pk)
print(f"✓ VideoUpload recuperado: {retrieved}")
```

**Resultado Esperado**:
```
<QuerySet []>
✓ VideoUpload creado: 1 - test.mp4 (PENDING)
✓ VideoUpload recuperado: 1 - test.mp4 (PENDING)
```

**Resultado Real**:
```
[COMPLETAR]
```

---

## 6. Resumen de Cambios

| Componente | Cambio | Estado |
|-----------|--------|--------|
| Modelos Django | 5 modelos con `managed=False` | ✅ |
| Script SQL | `001_fase2_analysis_tables.sql` creado y ejecutado | ✅ |
| Tablas BD | 5 tablas + índices + trigger | ✅ |
| Esquema BD.sql | Actualizado con nuevas tablas | ⏳ |
| Django Check | `python manage.py check` sin errores | ✅ |
| Django Shell | CRUD funcional | ⏳ |

---

## 7. Checklist Final

- [ ] Script SQL validado y ejecutado manualmente
- [ ] Tablas creadas en PostgreSQL (esquema Dev)
- [ ] Índices creados
- [ ] Trigger `fn_set_actualizadoen_analysis_report` funcional
- [ ] Esquema BD.sql actualizado
- [ ] Modelos Django sin errores (`manage.py check`)
- [ ] CRUD en Django shell validado
- [ ] Documento FASE_2_COMPLETADA.md completado

---

## 8. Próximos Pasos

Una vez completada Fase 2:

✅ **Avanzar a Fase 3**: Endpoints REST Básicos
- Crear `apps/analysis/serializers.py`
- Crear `apps/analysis/views.py`
- Implementar `/api/analysis/upload-video/` (POST)
- Implementar `/api/analysis/results/{video_id}/` (GET)

⚠️ **Prerequisitos para Fase 3**:
- Fase 2 completada y validada
- Tablas en BD funcionando
- Django ORM accediendo correctamente

---

## 📝 Notas

- **Auditoría**: Los campos `usuarioCreacion`, `fechaCreacion`, `usuarioModificacion`, `fechaModificacion` deben poblarse desde la aplicación.
- **idEmpresa**: Agregado para multi-tenancy. Requerido para filtros por empresa.
- **SystemParameter**: Global (sin idEmpresa). Para parámetros por empresa, usar `parametrosCabecera`/`parametroDetalle`.
- **Managed=False**: Los modelos no generan migraciones. Cambios de BD van en scripts SQL versionados.

---

**Documento actualizado**: [FECHA/HORA]  
**Revisado por**: [NOMBRE]  
**Aprobado para Fase 3**: [ ] SÍ / [ ] NO
