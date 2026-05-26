# Especificacion de Desarrollo del Proyecto

## Proposito

Este documento define las especificaciones tecnicas y normas de trabajo que se tendran en cuenta durante el desarrollo del nuevo backend distribuido del sistema.

Su objetivo es mantener una base ordenada, sostenible y facil de evolucionar mientras se realiza la migracion desde la arquitectura monolitica actual.

## Principios de desarrollo

El desarrollo se regira por principios SOLID y por una separacion clara de responsabilidades.

- Responsabilidad unica: cada modulo debe cumplir una sola funcion bien definida.
- Abierto/cerrado: el sistema debe permitir extensiones sin modificar excesivamente el codigo existente.
- Sustitucion de Liskov: los componentes intercambiables deben respetar el contrato esperado.
- Segregacion de interfaces: las dependencias deben exponerse por interfaces pequenas y concretas.
- Inversion de dependencias: el codigo de alto nivel no debe depender directamente de implementaciones rigidas.

Ademas de SOLID, se deben respetar estas reglas generales:

- Mantener codigo modular y facil de probar.
- Evitar logica de negocio mezclada con presentacion.
- Separar configuracion, infraestructura y dominio.
- Preferir nombres descriptivos y consistentes.

## Estructura de carpetas

La estructura del proyecto debe mantenerse clara y predecible.

Se recomienda:

- `src/` o `backend/` para el codigo principal del backend.
- `apps/` para las aplicaciones de dominio de Django.
- `services/` para logica de integracion o procesos especializados.
- `core/` para configuraciones base, utilidades comunes y componentes transversales.
- `scripts/` para scripts de mantenimiento, BD, despliegue o automatizacion.
- `docs/` para documentacion tecnica y de migracion.
- `static/` solo para recursos publicos realmente necesarios.
- `media/` o un directorio equivalente para archivos generados o cargados por usuarios.

Los nombres de carpetas deben ser consistentes, sin variaciones innecesarias, y en minusculas cuando sea posible.

## Manejo de carpetas y nombres

Se debe aplicar un control estricto sobre los nombres de carpetas, archivos y estructuras de sistema (Base de Datos).

- Evitar nombres ambiguos, abreviaturas poco claras o duplicadas.
- Usar nombres descriptivos que reflejen la funcion del contenido.
- No mezclar archivos de desarrollo con archivos de ejecucion.
- No guardar recursos temporales dentro de carpetas que forman parte del codigo productivo.

**Convenciones de Base de Datos y Modelos:**
- Usar formato **camelCase** tanto para los nombres de las Tablas (p. ej., `empresaUsuarioRol`, `menuOption`), como para nombres de sus columnas (p. ej., `codigoEmpresa`, `nombreOption`, `idUsuario`).
- En el ORM de Django (`models.py`), replicar exactamente el standard **camelCase** para sus variables. En aquellas columnas que formen parte de una base *legacy*, forzar su emparejamiento con parámetros como `db_column='codigoEmpresa'` dentro de los *Field properties*.

Ejemplos de nombres correctos en archivos y carpetas:

- `database_scripts`
- `migration_scripts`
- `seed_data`
- `training_videos`
- `generated_reports`

## Scripts de base de datos

Todos los scripts de creacion, actualizacion y mantenimiento de base de datos deben identificarse, versionarse y almacenarse en una carpeta especifica.

Se recomienda una estructura como esta:

- `scripts/db/create/` para scripts iniciales de creacion.
- `scripts/db/update/` para scripts incrementales de cambios.
- `scripts/db/fix/` para correcciones puntuales.
- `scripts/db/data/` para carga de datos base o semilla.

Reglas para estos scripts:

- Cada script debe tener un nombre secuencial y descriptivo.
- Debe quedar claro si crea, modifica o corrige estructura.
- **CONTROL MANUAL (NO AUTOMATICO)**: No se deben ejecutar scripts sin validacion previa y ejecucion manual explícita.
- Flujo de cambios en BD:
  1. Diseñar cambio y crear script SQL en `scripts/db/update/` con nombre secuencial (e.g., `002_fase3_endpoints_tables.sql`).
  2. **Validar**: Revisar el script manualmente en entorno dev/test, comprobar sintaxis y dependencias.
  3. **Documentar**: Actualizar `scripts/db/create/Esquema BD.sql` reflejando el nuevo estado del schema (tabla, columnas, FK, índices).
  4. **Ejecutar**: Correr el script en PostgreSQL (esquema Dev) de forma manual en el cliente psql o herramienta de BD.
  5. **Registrar**: Documentar en el archivo de control (FASE_X_COMPLETADA.md) qué script se ejecutó, cuándo y resultado.
- Debe existir trazabilidad de que script se ejecuto, en que orden, fecha y resultado en la documentacion de fase correspondiente.

## Auditoría

Todo registro creado o modificado en la base de datos debe ser auditado adecuadamente. 
Para los campos de auditoría (como `usuarioCreacion`, `usuarioModificacion`, etc.), se debe utilizar el ID del usuario (`idUsuario`) en lugar del correo electrónico (`correo`) o nombre de usuario. Si el usuario no está autenticado o el proceso es automático, se debe utilizar el identificador por defecto `'Sistema'`.

## Manejo de .gitignore

El proyecto debe tener un .gitignore bien definido para evitar subir archivos innecesarios, pesados o sensibles.

Se deben ignorar, como minimo:

- Entornos virtuales.
- Archivos compilados de Python.
- Credenciales y archivos sensibles de configuracion.
- Archivos temporales del sistema operativo o del editor.
- Resultados generados automaticamente que no deban versionarse.
- Archivos pesados de entrenamiento o modelos locales que no formen parte del despliegue controlado.

Tambien se debe revisar que no se incluyan por error:

- Logs de ejecucion.
- Caches.
- Archivos de prueba generados automaticamente.
- Exportaciones temporales.

## Separacion de archivos estaticos

Los archivos estaticos deben clasificarse segun su proposito para evitar desorden y facilitar el mantenimiento.

Se recomienda separar al menos estas categorias:

- Recursos publicos de la interfaz si llegaran a existir.
- Archivos generados por el sistema.
- Videos de entrenamiento.
- Videos de prueba.
- Imagenes de ejemplo.
- Archivos descargables o de reporte.

**Cambio en Fase 3**: Se introduce carpeta `backend/media/` centralizada para todos los uploads y archivos generados.

### Estructura Recomendada (Fase 3+)

```
backend/media/
├── images/
│   ├── uploads/              # Imágenes subidas sin procesar
│   │   └── image_20260503_143045.jpg
│   └── processed/            # Imágenes con YOLO + keypoints
│       └── image_keypoints_20260503_143045.jpg
├── videos/
│   ├── uploads/              # Videos sin procesar (desde POST /upload/)
│   │   └── video_20260503_143045.mp4
│   ├── processing/           # Videos siendo procesados con LSTM
│   │   └── video_processing_20260503_143045.mp4
│   └── results/              # Videos procesados + detectados
│       └── video_processed_20260503_143045.mp4
└── reports/                  # Reportes generados
    └── analysis_report_20260503.json
```

**Ventajas**:
- Centralización: Antes estaban en `Tesis/src/static/videos/`, ahora en un lugar único
- Claridad: Estados de procesamiento explícitos (uploads, processing, results)
- Escalabilidad: Fácil de migrar a almacenamiento externo (S3, Google Cloud Storage)
- Seguridad: Separado del código fuente, no se versionan en git

**Configuración en Django (core/settings.py)**:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

**En urls.py (desarrollo)**:
```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

En particular, los videos de entrenamiento deben mantenerse fuera de la carpeta de ejecucion principal si no son necesarios en produccion.

La recomendacion es almacenarlos en un espacio separado, por ejemplo:

- `resources/training_videos/`
- `resources/test_videos/`
- `resources/datasets/`
- `resources/models/`

Esto permite:

- Evitar mezclar contenido pesado con codigo fuente.
- Facilitar limpieza y despliegue.
- Reducir el riesgo de subir archivos innecesarios al repositorio.

## Convenciones de desarrollo

- Usar nombres claros para funciones, clases y variables.
- Mantener archivos pequenos y enfocados.
- Centralizar configuraciones repetidas.
- Documentar decisiones tecnicas importantes.
- Separar logica de negocio, acceso a datos y presentacion.
- Evitar dependencias innecesarias.

## Versionamiento y seguimiento

Todo cambio relevante debe quedar documentado y trazable.

- Las modificaciones estructurales deben quedar registradas en documentacion.
- Los scripts de BD deben versionarse junto con la funcionalidad que soportan.
- Los recursos pesados o generados deben revisarse antes de ser incluidos en el repositorio.

## CI/CD y Despliegue

Para garantizar un ciclo de vida de desarrollo agil y seguro, se deben considerar las siguientes practicas de Integracion y Despliegue Continuo (CI/CD):

- **Contenerizacion (Docker):** Encapsular la aplicacion (backend, Celery workers, Redis, etc.) en contenedores para asegurar que funcione igual en desarrollo, pruebas y produccion.
- **Pipelines Automatizados:** Configurar flujos de CI (por ejemplo, en GitHub Actions o GitLab CI) que ejecuten analisis de codigo (Linting/Flake8), pruebas unitarias y analisis de seguridad por cada Pull Request o cambio principal.
- **Agnosticismo de Entorno (12-Factor App):** Toda configuracion que varíe entre entornos (credenciales, URLs de base de datos, claves secretas) debe inyectarse exclusivamente mediante variables de entorno (`.env`), nunca hardcodeada.
- **Despliegues Predecibles:** Las migraciones de base de datos y recoleccion de estaticos (`collectstatic`) deben ejecutarse automaticamente en la fase de release o despliegue antes de habilitar el trafico al nuevo codigo.

## Orden de aplicacion

Estas especificaciones deben considerarse antes de comenzar la implementacion formal del backend.

1. Definir estructura base de carpetas.
2. Preparar el .gitignore.
3. Crear la carpeta de scripts de base de datos.
4. Separar recursos estaticos y archivos pesados.
5. Establecer la estructura Django por apps y servicios.
6. Aplicar principios SOLID en cada modulo nuevo.

## Nota final

Este documento funciona como referencia tecnica de desarrollo. Si durante la migracion se identifican nuevas reglas de organizacion o convenciones, este archivo debe actualizarse para mantener coherencia con la arquitectura objetivo.