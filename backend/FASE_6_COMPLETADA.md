# FASE 6: MIGRACIÓN DE AUTENTICACION COMPLETADA

## Objetivo
Migrar el sistema de login y permisos del legado Flask al nuevo backend en Django, utilizando JWT para proteger los endpoints.

## Tareas Realizadas

1. **Creación de los Endpoints de Autenticación**:
   - **Login**:
     - **URL**: `/api/users/login/` (POST)
     - **Controlador**: `AuthViewSet.login` en `backend/apps/users/views.py`.
     - **Descripción**: Autentica al usuario usando encriptación SHA256 para el password (compatibilidad con Flask legacy). Retorna los datos del usuario y un token JWT válido.
   - **Registro (Creación de Usuario)**:
     - **URL**: `/api/users/usuarios/` (POST)
     - **Controlador**: `UsersViewSet` (heredado de `ModelViewSet`) en `backend/apps/users/views.py`.
     - **Descripción**: Permite el registro o creación de un nuevo usuario en la plataforma enviando los datos correspondientes.

2. **Implementación de JSON Web Tokens (JWT)**:
   - Instalación de la librería `pyjwt`.
   - Se creó `CustomJWTAuthentication` en `backend/apps/users/authentication.py` para emitir y validar llaves de sesión (JWT) utilizando como carga útil el idUsuario.

3. **Protección de Endpoints IA**:
   - Ajuste en `backend/core/settings.py` incluyendo `IsAuthenticated` como política por defecto en todo `REST_FRAMEWORK`.
   - La API ahora devuelve HTTP `401 Unauthorized` si no existe la cabecera `Authorization: Bearer <token>`.

4. **Validar Autorización en Análisis Propios**:
   - En `backend/apps/analysis/views.py`, en el controlador `VideoAnalysisViewSet` se modificó el método asincrónico para asignar videos al usuario propietario al cargarse.
   - El listado e interacción (`get_queryset`) ahora filtra estrictamente por `self.request.user`, permitiendo sólo a los dueños ver y modificar archivos y sus reportes.

## Endpoints Configurados para Uso

A continuación se listan los endpoints principales habilitados en esta fase:

### 1. Iniciar Sesión (Login)
- **Ruta**: `POST /api/users/login/`
- **Permisos**: Público (`AllowAny`)
- **Body (JSON)**:
  ```json
  {
    "correo": "usuario@ejemplo.com",
    "password": "mi_password_secreto"
  }
  ```
- **Respuesta Exitosa (200 OK)**:
  ```json
  {
    "token": "eyJ0eXAi... (token JWT)",
    "user": {
      "idUsuario": 1,
      "nombre": "Juan",
      "apellido": "Pérez",
      "correo": "usuario@ejemplo.com",
      "ultimoIngreso": "2026-05-10T15:30:00Z"
      // ... otros campos
    }
  }
  ```

### 2. Registro / Creación de cuenta
- **Ruta**: `POST /api/users/usuarios/`
- **Permisos**: Público (`AllowAny` temporalmente para permitir registrarse sin token previo, sujeto a ajuste según reglas de negocio finales)
- **Body (JSON)**:
  ```json
  {
    "nombre": "Juan",
    "apellido": "Pérez",
    "cedula": "1234567890",
    "correo": "usuario@ejemplo.com",
    "password": "mi_password_secreto"
  }
  ```

### 3. Listado y Gestión de Usuarios (CRUD)
- **Listar**: `GET /api/users/usuarios/`
- **Obtener uno**: `GET /api/users/usuarios/{id}/`
- **Actualizar**: `PUT /api/users/usuarios/{id}/`
- **Eliminar**: `DELETE /api/users/usuarios/{id}/`
- **Permisos**: Requieren Token JWT (`Authorization: Bearer <token>`).

***

## Criterio de Éxito Cumplido
✅ El Login devuelve un JWT completamente válido.
✅ Los endpoints principales rechazan las peticiones anónimas sin token.
