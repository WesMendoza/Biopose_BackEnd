# Biopose BackEnd - Sistema Distribuido Django

Este es el nuevo backend principal del proyecto BioPose para deteccion y analisis de posturas, en proceso de migracion a una arquitectura moderna y escalable. Todo el sistema logico ahora reside sobre Django, con PostgreSQL como base de datos, y en capas preparadas para usar Celery, Redis y Channels.

## Requisitos Previos

Antes de levantar el proyecto, asegurate de contar con:
1. **Python 3.10+** instalado en tu maquina.
2. **PostgreSQL** instalado y ejecutandose.
3. El archivo `.env` configurado dentro de la carpeta `backend/`.

## Pasos para inicializacion (Primera vez)

Si es la primera vez que clonas o descargas el proyecto, debes seguir estos pasos para prepararlo en tu entorno local.

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

py .\manage.py runserver 0.0.0.0:8000