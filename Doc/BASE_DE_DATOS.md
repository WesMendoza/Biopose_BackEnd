# Guía de Base de Datos y Sincronización (PostgreSQL / Django)

Este documento detalla la estrategia de base de datos del proyecto BioPose, el uso de scripts SQL manuales vs. migraciones Django, y cómo utilizar la herramienta de validación para asegurar la consistencia del esquema.

---

## 📂 Índice
1. [Estrategia de la Base de Datos](#1-estrategia-de-la-base-de-datos)
2. [El Dilema: Script SQL vs. Migraciones Django](#2-el-dilema-script-sql-vs-migraciones-django)
3. [Cómo Sincronizar: El comando `--fake-initial`](#3-cómo-sincronizar-el-comando---fake-initial)
4. [Validador de Base de Datos (`check_db.py`)](#4-validador-de-base-de-datos-check_dbpy)

---

## 1. Estrategia de la Base de Datos
El backend de BioPose utiliza **PostgreSQL** como motor principal de base de datos.
La estructura consta de:
* Un esquema llamado **`Dev`**.
* Tablas maestras, transaccionales y tablas específicas del módulo de análisis de IA (para imágenes, videos, eventos y reportes agregados).
* Tipos de datos avanzados como `JSONB` e índices `GIN` para almacenar y consultar de forma ultra rápida las coordenadas de los keypoints corporales.

---

## 2. El Dilema: Script SQL vs. Migraciones Django
En el ciclo de desarrollo de BioPose existen dos recursos para estructurar la base de datos:

1. **[CreateDb.sql](/Biopose_BackEnd/backend/scripts/db/create/CreateDb.sql) (Script SQL):**
   * Es la definición pura y nativa en PostgreSQL.
   * Crea las tablas del negocio, esquemas, índices y funciones/triggers de PostgreSQL.
   * **Problema:** Django desconoce que estas tablas existen, ya que no se crearon a través de su motor de migraciones (`django_migrations` se encuentra vacío).

2. **Migraciones de Django (`python manage.py migrate`):**
   * Es el mecanismo automático de Django para estructurar la base de datos a partir de los modelos de Python.
   * **Problema:** Si se ejecuta directamente, dará error porque intentará volver a crear tablas que el script SQL ya creó. Además, Django requiere crear sus propias tablas de control de sesión y administración (`auth`, `admin`, `sessions`) que no están en el script SQL.

---

## 3. Cómo Sincronizar: El comando `--fake-initial`
Para resolver este conflicto, cuando levantas la base de datos por primera vez usando el script manual SQL, debes ejecutar el siguiente comando para registrar las tablas ante Django sin intentar recrearlas:

```powershell
python manage.py migrate --fake-initial
```

### ¿Qué hace este comando?
1. Django examina las migraciones existentes.
2. Si detecta que una tabla definida en la migración inicial (por ejemplo, `users` o `empresa`) ya existe físicamente en PostgreSQL (creada por tu Script SQL), **omite su creación (la marca como falsa/completada)**.
3. Procede a crear únicamente las tablas del sistema que hacen falta (administración, sesiones, etc.).

---

## 4. Validador de Base de Datos (`check_db.py`)
Para verificar que todas las tablas del proyecto y de Django existan y estén en orden, se ha implementado el script [check_db.py](/Biopose_BackEnd/backend/scripts/db/check_db.py).

### Cómo Ejecutar el Validador
Abre una terminal en la carpeta `backend/` con tu entorno virtual activo y ejecuta:

```powershell
python scripts/db/check_db.py
```

### ¿Qué verifica el Script?
1. **Conexión:** Prueba la conexión a la base de datos usando las credenciales del `.env` o `.env.local` activo.
2. **Tablas del Negocio:** Comprueba la presencia de las 14 tablas maestras y transaccionales del proyecto:
   * `users`
   * `empresa`
   * `rol`
   * `menuOption`
   * `systemParameter`
   * `empresaUsuarioRol`
   * `rolOption`
   * `parametrosCabecera`
   * `parametroDetalle`
   * `analysisImageUpload`
   * `analysisVideoUpload`
   * `analysisDetectionEvent`
   * `analysisPersonKeypoints`
   * `analysisReport`
3. **Tablas de Control de Django:** Comprueba la presencia de las tablas internas del framework:
   * `django_migrations`
   * `django_content_type`
   * `django_session`
   * `auth_permission`
   * `auth_group`
   * `django_admin_log`
4. **Diagnóstico:** Si falta alguna tabla, el script te ofrecerá la recomendación exacta sobre qué comandos o scripts ejecutar para corregirla.
