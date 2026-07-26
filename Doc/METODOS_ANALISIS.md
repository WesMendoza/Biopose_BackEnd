# Documentación de Endpoints y Métodos de la API (BioPose)

Este documento detalla los endpoints HTTP (API REST), WebSockets (Django Channels) y tareas en segundo plano (Celery) implementados en el sistema de BioPose.

---

## 📂 Índice

1. [API de Autenticación (Auth)](#1-api-de-autenticación-auth)
2. [API de Gestión de Usuarios (Users)](#2-api-de-gestión-de-usuarios-users)
3. [API de Gestión de Empresas (Empresas)](#3-api-de-gestión-de-empresas-empresas)
4. [API de Gestión de Roles (Roles)](#4-api-de-gestión-de-roles-roles)
5. [API de Asignación de Roles a Usuarios (UserRoles)](#5-api-de-asignación-de-roles-a-usuarios-userroles)
6. [API de Opciones de Menú y Accesos (MenuOptions)](#6-api-de-opciones-de-menú-y-accesos-menuoptions)
7. [API de Configuración Global de Rutas y Parámetros (RutasConfig)](#7-api-de-configuración-global-de-rutas-y-parámetros-rutasconfig)
8. [API de Gestión de Archivos (Media)](#8-api-de-gestión-de-archivos-media)
9. [API de Estimación de Pose en Imágenes (Pose)](#9-api-de-estimación-de-pose-en-imágenes-pose)
10. [API de Procesamiento y Clasificación de Video (Behavior)](#10-api-de-procesamiento-y-clasificación-de-video-behavior)
11. [API de Detección en Tiempo Real (Live - SSE & WebSockets)](#11-api-de-detección-en-tiempo-real-live---sse--websockets)
12. [Tareas en Segundo Plano (Celery Tasks)](#12-tareas-en-segundo-plano-celery-tasks)

---

## 1. API de Autenticación (Auth)

Implementada en [views.py](/Biopose_BackEnd/backend/apps/authentication/views.py) y enrutada en [urls.py](/Biopose_BackEnd/backend/apps/authentication/urls.py) con el prefijo `/api/auth/`.

### A. Iniciar Sesión (Login)

- **URL:** `/api/auth/login/`
- **Método:** `POST`
- **Descripción:** Recibe el correo y la contraseña, valida las credenciales y genera un token JWT de acceso para el usuario.
- **Payload (Body - JSON):**
  - `correo` (String): Correo electrónico del usuario.
  - `password` (String): Contraseña del usuario.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Inicio de sesión exitoso",
    "detalle": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
  ```

### B. Registrar Cuenta (Register)

- **URL:** `/api/auth/registerAccount/`
- **Método:** `POST`
- **Descripción:** Registra un nuevo usuario en el sistema. Soporta dos flujos: crear una nueva empresa (haciendo al usuario su administrador y configurando los accesos base) o unirse a una empresa existente como invitado mediante su código de empresa.
- **Payload (Body - JSON):**
  - `nombre` (String): Nombre del usuario.
  - `apellido` (String): Apellido del usuario.
  - `cedula` (String): Cédula de identidad.
  - `correo` (String): Correo electrónico.
  - `password` (String): Contraseña.
  - `codigoEmpresa` (String - Opcional): Código de la empresa a la que se desea unir (si `isCrearEmpresa` es falso).
  - `isCrearEmpresa` (Boolean - Opcional): `true` si el usuario registrará una nueva empresa.
  - `nombreEmpresa` (String - Opcional): Nombre de la empresa a crear.
  - `rucEmpresa` (String - Opcional): RUC de la empresa a crear.
- **Respuesta (201 Created):**
  ```json
  {
    "codigo": 201,
    "mensaje": "Cuenta creada exitosamente",
    "detalle": {
      "idUsuario": 5,
      "nombre": "Juan",
      "apellido": "Pérez",
      "cedula": "0999999999",
      "correo": "juan.perez@example.com",
      "estado": "A",
      "ultimoIngreso": null
    }
  }
  ```

### C. Verificar Cédula

- **URL:** `/api/auth/verifyCedula/`
- **Método:** `POST`
- **Descripción:** Comprueba si la cédula ingresada ya se encuentra registrada en la base de datos para evitar duplicados.
- **Payload (Body - JSON):**
  - `cedula` (String): Cédula a verificar.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Verificación completada",
    "detalle": {
      "exists": true
    }
  }
  ```

### D. Verificar Correo

- **URL:** `/api/auth/verifyEmail/`
- **Método:** `POST`
- **Descripción:** Comprueba si el correo electrónico ingresado ya se encuentra registrado en el sistema.
- **Payload (Body - JSON):**
  - `correo` (String): Correo a verificar.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Verificación completada",
    "detalle": {
      "exists": false
    }
  }
  ```

### E. Listar Empresas Activas (Público)

- **URL:** `/api/auth/empresas-publicas/`
- **Método:** `GET`
- **Descripción:** Obtiene un listado de las empresas activas registradas para seleccionarlas en el combo box de registro del Frontend.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Lista de empresas",
    "detalle": [
      { "codigoEmpresa": "EMP001", "nombreEmpresa": "Mi Empresa S.A." }
    ]
  }
  ```

---

## 2. API de Gestión de Usuarios (Users)

Implementada en [views.py](/Biopose_BackEnd/backend/apps/users/views.py) y enrutada en [urls.py](/Biopose_BackEnd/backend/apps/users/urls.py) con el prefijo `/api/users/`. Requiere token de autenticación (JWT).

### A. Listar Usuarios

- **URL:** `/api/users/`
- **Método:** `GET`
- **Query Parameters (Opcionales):**
  - `idEmpresa` o `empresa_id` (Integer): Filtra por la empresa a la que pertenecen los usuarios.
  - `idRol` o `rol_id` (Integer): Filtra por el rol asignado a los usuarios.
- **Descripción:** Obtiene la lista de todos los usuarios registrados (activos e inactivos). Si se filtra por `idEmpresa`, realiza una anotación que añade `idRol` y `nombreRol` directamente en los objetos de respuesta para facilitar su uso en el frontend.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Lista de usuarios obtenida exitosamente",
    "detalle": [
      {
        "idUsuario": 1,
        "nombre": "Admin",
        "apellido": "Sistema",
        "cedula": "1234567890",
        "correo": "admin@biopose.com",
        "estado": "A",
        "ultimoIngreso": "2026-07-14T20:50:00Z",
        "idRol": 1,
        "nombreRol": "Administrador"
      }
    ]
  }
  ```

### B. Obtener Detalle de Usuario (por ID)

- **URL:** `/api/users/<int:id_usuario>/`
- **Método:** `GET`
- **Descripción:** Obtiene los detalles de perfil completos de un usuario a partir de su ID primario.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Usuario obtenido exitosamente",
    "detalle": {
      "idUsuario": 1,
      "nombre": "Admin",
      "apellido": "Sistema",
      "cedula": "1234567890",
      "correo": "admin@biopose.com",
      "estado": "A",
      "ultimoIngreso": "2026-07-14T20:50:00Z"
    }
  }
  ```

### C. Crear Usuario (Manual/Administrativo)

- **URL:** `/api/users/`
- **Método:** `POST`
- **Descripción:** Crea un nuevo usuario en la base de datos (con contraseña cifrada/hasheada).
- **Payload (Body - JSON):**
  - `nombre` (String): Nombre.
  - `apellido` (String): Apellido.
  - `cedula` (String): Cédula.
  - `correo` (String): Correo.
  - `password` (String): Contraseña en texto plano.
- **Respuesta (201 Created):**
  ```json
  {
    "codigo": 201,
    "mensaje": "Usuario creado exitosamente",
    "detalle": {
      "idUsuario": 6,
      "nombre": "Empleado",
      "apellido": "Prueba",
      "cedula": "0999999998",
      "correo": "empleado@biopose.com",
      "estado": "A",
      "ultimoIngreso": null
    }
  }
  ```

### D. Obtener Usuario por Cédula

- **URL:** `/api/users/cedula/<str:cedula>/`
- **Método:** `GET`
- **Descripción:** Obtiene los detalles de un usuario buscando directamente por su número de cédula (solo para usuarios activos).
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Usuario obtenido exitosamente",
    "detalle": {
      "idUsuario": 6,
      "nombre": "Empleado",
      "apellido": "Prueba",
      "cedula": "0999999998",
      "correo": "empleado@biopose.com",
      "estado": "A",
      "ultimoIngreso": null
    }
  }
  ```

### E. Actualizar Usuario por Cédula

- **URL:** `/api/users/actualizarPorCedula/<str:cedula>/`
- **Método:** `PUT` / `PATCH`
- **Descripción:** Actualiza los datos de un usuario buscándolo por cédula. Admite actualizaciones parciales (`PATCH`). Si el estado del usuario es actualizado a `'A'` (Activo/Reactivado), reactiva también automáticamente su rol de empresa.
- **Payload (Body - JSON):** Campos a actualizar (ej: `nombre`, `apellido`, `estado`, etc.).
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Usuario actualizado exitosamente",
    "detalle": {
      "idUsuario": 6,
      "nombre": "Empleado",
      "apellido": "Editado",
      "cedula": "0999999998",
      "correo": "empleado@biopose.com",
      "estado": "A",
      "ultimoIngreso": null
    }
  }
  ```

### F. Eliminar Usuario (Borrado Lógico)

- **URL:** `/api/users/eliminar/<str:cedula>/`
- **Método:** `DELETE`
- **Descripción:** Realiza la baja lógica de un usuario a partir de su cédula. Cambia el campo `estado` del usuario a `'N'` (Inactivo) y realiza la misma desactivación en su asignación de rol (`EmpresaUsuarioRol`).
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Usuario eliminado exitosamente.",
    "detalle": null
  }
  ```

---

## 3. API de Gestión de Empresas (Empresas)

Implementada en [views.py](/Biopose_BackEnd/backend/apps/gestionEmpresas/views.py) y enrutada en [urls.py](/Biopose_BackEnd/backend/apps/gestionEmpresas/urls.py) con la ruta `/api/gestionEmpresas/empresas/`. Requiere token de autenticación (JWT).

### A. Listar Empresas

- **URL:** `/api/gestionEmpresas/empresas/`
- **Método:** `GET`
- **Descripción:** Obtiene un listado de todas las empresas registradas.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Lista de empresas obtenida exitosamente",
    "detalle": [
      {
        "idEmpresa": 1,
        "codigoEmpresa": "EMP001",
        "nombreEmpresa": "Mi Empresa",
        "ruc": "1799999999001",
        "estado": "A"
      }
    ]
  }
  ```

### B. Obtener Detalle de Empresa

- **URL:** `/api/gestionEmpresas/empresas/<int:idEmpresa>/`
- **Método:** `GET`
- **Descripción:** Obtiene el detalle completo de una empresa específica.

### C. Crear Empresa

- **URL:** `/api/gestionEmpresas/empresas/`
- **Método:** `POST`
- **Descripción:** Registra una nueva empresa en el sistema y autogenera de forma secuencial su `codigoEmpresa` (ej: `EMP004`).
- **Payload (Body - JSON):**
  - `nombreEmpresa` (String): Nombre comercial o razón social.
  - `ruc` (String): Registro Único de Contribuyentes.
- **Respuesta (201 Created):**
  ```json
  {
    "codigo": 201,
    "mensaje": "Empresa creada exitosamente",
    "detalle": {
      "idEmpresa": 4,
      "codigoEmpresa": "EMP004",
      "nombreEmpresa": "Nueva Empresa S.A.",
      "ruc": "0999999997001",
      "estado": "A"
    }
  }
  ```

### D. Actualizar Empresa

- **URL:** `/api/gestionEmpresas/empresas/<int:idEmpresa>/`
- **Método:** `PUT` / `PATCH`
- **Descripción:** Modifica los atributos de una empresa existente.

### E. Eliminar / Desactivar Empresa (Baja Lógica)

- **URL:** `/api/gestionEmpresas/empresas/<int:idEmpresa>/`
- **Método:** `DELETE`
- **Descripción:** Realiza un borrado lógico estableciendo el estado de la empresa a `'N'`.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Empresa eliminada exitosamente.",
    "detalle": null
  }
  ```

### F. Asignar Empresa (por Código y Cédula)

- **URL:** `/api/gestionEmpresas/empresas/asignarEmpresa/`
- **Método:** `POST`
- **Descripción:** Asocia a un usuario con una empresa en base a su número de cédula y el código de la empresa. El usuario ingresa inicialmente sin ningún rol asignado (`idRol = null`).
- **Payload (Body - JSON):**
  - `codigoEmpresa` (String): Código único de la empresa.
  - `cedula` (String): Cédula de identidad del usuario.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Usuario asignado a la empresa de forma exitosa.",
    "detalle": { ... }
  }
  ```

---

## 4. API de Gestión de Roles (Roles)

Implementada en [views.py](/Biopose_BackEnd/backend/apps/gestionEmpresas/views.py) y enrutada en [urls.py](/Biopose_BackEnd/backend/apps/gestionEmpresas/urls.py) con la ruta `/api/gestionEmpresas/roles/`. Requiere token de autenticación (JWT).

### A. Listar Roles

- **URL:** `/api/gestionEmpresas/roles/`
- **Método:** `GET`
- **Query Parameters (Opcional):**
  - `idEmpresa` o `empresa_id` (Integer): ID de la empresa para filtrar los roles asociados.
- **Descripción:** Lista los roles configurados. Si se es administrador, permite ver los de su empresa.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Lista de roles obtenida exitosamente",
    "detalle": [
      {
        "idRol": 1,
        "idEmpresa": 1,
        "nombreRol": "Administrador",
        "estado": "A"
      }
    ]
  }
  ```

### B. Crear Rol

- **URL:** `/api/gestionEmpresas/roles/`
- **Método:** `POST`
- **Descripción:** Registra un nuevo rol dentro de la empresa. Solo permitido para administradores de la misma.
- **Payload (Body - JSON):**
  - `nombreRol` (String): Nombre para el rol (ej: `'Supervisor'`).
  - `idEmpresa` (Integer): ID de la empresa asociada.
- **Respuesta (201 Created):**
  ```json
  {
    "codigo": 201,
    "mensaje": "Rol creado exitosamente",
    "detalle": { ... }
  }
  ```

### C. Actualizar Rol

- **URL:** `/api/gestionEmpresas/roles/<int:idRol>/`
- **Método:** `PUT` / `PATCH`
- **Descripción:** Modifica las propiedades del rol (ej. `nombreRol` o `estado`).

### D. Eliminar Rol (Baja Lógica)

- **URL:** `/api/gestionEmpresas/roles/<int:idRol>/`
- **Método:** `DELETE`
- **Descripción:** Da de baja lógica al rol estableciendo su estado a `'N'`.

---

## 5. API de Asignación de Roles a Usuarios (UserRoles)

Implementada en [views.py](/Biopose_BackEnd/backend/apps/gestionEmpresas/views.py) y enrutada en [urls.py](/Biopose_BackEnd/backend/apps/gestionEmpresas/urls.py) con la ruta `/api/gestionEmpresas/asignarUsuarioRol/`. Requiere token de autenticación (JWT).

### A. Crear Asignación de Usuario, Empresa y Rol

- **URL:** `/api/gestionEmpresas/asignarUsuarioRol/`
- **Método:** `POST`
- **Descripción:** Asigna explícitamente una empresa y un rol a un usuario determinado.
- **Payload (Body - JSON):**
  - `idUsuario` (Integer): ID del usuario.
  - `idEmpresa` (Integer): ID de la empresa.
  - `idRol` (Integer): ID del rol a otorgar.
- **Respuesta (201 Created):**
  ```json
  {
    "codigo": 201,
    "mensaje": "Asignación creada exitosamente",
    "detalle": { ... }
  }
  ```

### B. Reasignar Rol

- **URL:** `/api/gestionEmpresas/asignarUsuarioRol/reasignar/`
- **Método:** `PUT` / `PATCH`
- **Descripción:** Cambia el rol de un usuario dentro de su asignación de empresa activa. Solo administradores.
- **Payload (Body - JSON):**
  - `idUsuario` (Integer): ID del usuario.
  - `idRol` (Integer): Nuevo ID de rol a asignar.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Rol reasignado correctamente.",
    "detalle": { "idEmpresaUsuarioRol": 15 }
  }
  ```

### C. Desasignar Rol (Quitar Rol)

- **URL:** `/api/gestionEmpresas/asignarUsuarioRol/eliminar/`
- **Método:** `PUT`
- **Descripción:** Remueve el rol asignado a un usuario (dejándolo como `idRol = null`) en su registro activo de la empresa.
- **Payload (Body - JSON):**
  - `idUsuario` (Integer) o `cedula` (String): Identificador del usuario.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Se han desasignado el rol del usuario.",
    "detalle": { "idUsuario": 6 }
  }
  ```

---

## 6. API de Opciones de Menú y Accesos (MenuOptions)

Implementada en [views.py](/Biopose_BackEnd/backend/apps/menuOpciones/views.py) y enrutada en [urls.py](/Biopose_BackEnd/backend/apps/menuOpciones/urls.py) bajo la ruta `/api/menuOpciones/opciones/` y `/api/menuOpciones/asignarRolOpcion/`. Requiere token de autenticación (JWT).

### A. Listar Opciones de Menú (Globales)

- **URL:** `/api/menuOpciones/opciones/`
- **Método:** `GET`
- **Descripción:** Obtiene todas las opciones y rutas de navegación generales habilitadas en la aplicación.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Lista de opciones de menú obtenida exitosamente",
    "detalle": [
      {
        "idOption": 1,
        "nombreOption": "Dashboard",
        "ruta": "/app/dashboard",
        "estado": "A"
      }
    ]
  }
  ```

### B. Listar Opciones Permitidas por Usuario

- **URL:** `/api/menuOpciones/opciones/usuario/<int:idUsuario>/`
- **Método:** `GET`
- **Descripción:** Resuelve y retorna las opciones de menú y rutas del frontend a las que tiene acceso el usuario especificado, cruzando su rol actual y las asignaciones Rol-Opción.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Opciones de menú del usuario 6 obtenidas exitosamente.",
    "detalle": [
      {
        "idRolOption": 12,
        "idRol": 2,
        "idOption": 1,
        "nombreOption": "Dashboard",
        "ruta": "/app/dashboard",
        "estado": "A"
      }
    ]
  }
  ```

### C. Asignar Opciones a un Rol

- **URL:** `/api/menuOpciones/asignarRolOpcion/`
- **Método:** `POST`
- **Descripción:** Vincula una o múltiples opciones de menú a un rol específico de la empresa. Solo para administradores.
- **Payload (Body - JSON):**
  ```json
  {
    "idRol": 2,
    "idOptions": [1, 2, 3]
  }
  ```
  _(También se puede usar `"idOption": 1` en lugar de `"idOptions"` para una asignación individual)_
- **Respuesta (201 Created / 200 OK):**
  ```json
  {
    "codigo": 201,
    "mensaje": "Proceso de asignación completado.",
    "detalle": {
      "asignadas": [{ "idRolOption": 18, "idRol": 2, "idOption": 1 }],
      "omitidasPorDuplicidad": []
    }
  }
  ```

### D. Desasignar Opción de un Rol

- **URL:** `/api/menuOpciones/asignarRolOpcion/desasignar/`
- **Método:** `POST`
- **Descripción:** Desvincula e inhabilita (pone estado = `'I'`) una opción de menú asociada a un rol.
- **Payload (Body - JSON):**
  - `idRol` (Integer): ID del rol.
  - `idOption` (Integer): ID de la opción a desasignar.
- **Respuesta (200 OK):**
  ```json
  {
    "codigo": 200,
    "mensaje": "Opción desasignada del rol exitosamente (estado = I).",
    "detalle": { "idRolOption": 18, "idRol": 2, "idOption": 1 }
  }
  ```

---

## 7. API de Configuración Global de Rutas y Parámetros (RutasConfig)

Implementada en [views.py](/Biopose_BackEnd/backend/apps/menuOpciones/views.py) y enrutada en [urls.py](/Biopose_BackEnd/backend/apps/menuOpciones/urls.py) con la ruta `/api/menuOpciones/rutas/configurar/`. Requiere token de autenticación (JWT).

### A. Obtener Configuración Global por Empresa

- **URL:** `/api/menuOpciones/rutas/configurar/`
- **Método:** `GET`
- **Query Parameters:**
  - `idEmpresa` (Integer): ID de la empresa de la cual obtener la configuración.
- **Descripción:** Devuelve un listado con los parámetros clave-valor configurados para el comportamiento de la empresa (ej: límites de subida de video, umbrales del modelo, etc.).
- **Respuesta (200 OK):**
  ```json
  [
    { "codigo": "LIMITE_VIDEOS_MB", "valor": "50" },
    { "codigo": "CONFIDENCE_POSE_MIN", "valor": "0.70" }
  ]
  ```

### B. Guardar o Actualizar Parámetro por Empresa

- **URL:** `/api/menuOpciones/rutas/configurar/`
- **Método:** `POST`
- **Descripción:** Agrega o actualiza dinámicamente un parámetro clave-valor vinculándolo a una cabecera de parámetros exclusiva de la empresa (`CONF_SISTEMA_EMP_<idEmpresa>`).
- **Payload (Body - JSON):**
  - `idEmpresa` (Integer): ID de la empresa.
  - `codigo` (String): Código clave del parámetro.
  - `valor` (String): Valor del parámetro.
- **Respuesta (200 OK):**
  ```json
  {
    "success": true,
    "message": "Parámetro de empresa guardado exitosamente.",
    "codigo": "LIMITE_VIDEOS_MB",
    "valor": "50",
    "idEmpresa": 1
  }
  ```

---

## 8. API de Gestión de Archivos (Media)

Implementada en [media/views.py](/Biopose_BackEnd/backend/apps/analysis/api/media/views.py) y enrutada en [media/urls.py](/Biopose_BackEnd/backend/apps/analysis/api/media/urls.py).

### A. Subir Imagen

- **URL:** `/api/analysis/media/images/upload/`
- **Método:** `POST`
- **Parser:** `MultipartForm`
- **Descripción:** Sube una imagen en bruto al servidor y registra un objeto `ImageUpload` en la base de datos con estado `PENDING`. Limita el peso a un máximo de 10 MB.
- **Payload (Body - form-data):**
  - `image` (File): Archivo de la imagen (`.png`, `.jpg`, `.jpeg`).
- **Respuesta (201 Created):**
  ```json
  {
    "idImageUpload": 1,
    "nombreOriginal": "mi_foto.jpg",
    "rutaArchivoOriginal": "images/uploads/img_e23a41bc.jpg",
    "tamanioBytes": 204850,
    "estado": "PENDING"
  }
  ```

### B. Subir Video

- **URL:** `/api/analysis/media/videos/upload/`
- **Método:** `POST`
- **Parser:** `MultipartForm`
- **Descripción:** Sube un video en bruto al servidor y registra un objeto `VideoUpload` en la base de datos con estado `PENDING`. Limita el peso a 50 MB. Dispara de forma pasiva una tarea de limpieza de archivos obsoletos.
- **Payload (Body - form-data):**
  - `video` (File): Archivo de video (`.mp4`, `.webm`, etc.).
- **Respuesta (201 Created):**
  ```json
  {
    "idVideoUpload": 10,
    "nombreOriginal": "grabacion_seguridad.mp4",
    "rutaArchivo": "videos/uploads/vid_8fb39d10.mp4",
    "tamanioBytes": 12450890,
    "estado": "PENDING"
  }
  ```

### C. Eliminar / Limpiar Video y Reporte

- **URL:** `/api/analysis/media/videos/<int:video_id>/`
- **Método:** `DELETE`
- **Descripción:** Elimina físicamente del almacenamiento del servidor el video original (`.mp4`), su respectivo archivo de keypoints JSON (`.json`) y el registro de la base de datos.
- **Respuesta (200 OK):**
  ```json
  {
    "message": "Archivos y datos destruidos correctamente"
  }
  ```

---

## 9. API de Estimación de Pose en Imágenes (Pose)

Implementada en [pose/views.py](/Biopose_BackEnd/backend/apps/analysis/api/pose/views.py) y enrutada en [pose/urls.py](/Biopose_BackEnd/backend/apps/analysis/api/pose/urls.py).

### A. Procesar Imagen con YOLOv8-pose

- **URL:** `/api/analysis/pose/image/<int:image_id>/process/`
- **Método:** `POST`
- **Descripción:** Toma la imagen con el ID especificado, la procesa mediante YOLOv8-pose para extraer los puntos clave (keypoints) de las personas detectadas, genera una imagen procesada con el esqueleto dibujado en `media/images/processed/` y un archivo JSON de reporte.
- **Respuesta (200 OK):**
  ```json
  {
    "success": true,
    "model_used": "yolov8s-pose",
    "position": "unknown",
    "persons_detected": 1,
    "processed_image_path": "images/processed/pose_f3b928ec.jpg",
    "persons": [
      {
        "person_id": 0,
        "bbox": { "x1": 0, "y1": 0, "x2": 0, "y2": 0 },
        "keypoints": [
          {
            "id": 0,
            "name": "nose",
            "x": 340.5,
            "y": 150.2,
            "confidence": 0.95
          }
          // ... 17 puntos COCO totales
        ]
      }
    ]
  }
  ```

### B. Descargar Dataset de Imagen Única

- **URL:** `/api/analysis/pose/image/<int:image_id>/save-to-disk/`
- **Método:** `POST`
- **Descripción:** Genera un archivo ZIP descargable que contiene la imagen y el archivo JSON con los keypoints. Posterior al empaquetamiento, elimina físicamente los archivos del servidor y remueve el registro de la base de datos para ahorrar espacio.
- **Payload (Body - JSON):**
  - `results` (Object): Los keypoints (editados o finales) devueltos por el frontend.
  ```json
  {
    "results":
  }
  ```
- **Respuesta (200 OK):**
  - Retorna un archivo binario ZIP: `Dataset_Imagen_<image_id>.zip`

### C. Descargar Dataset por Lotes (Batch)

- **URL:** `/api/analysis/pose/batch/save-to-disk/`
- **Método:** `POST`
- **Descripción:** Agrupa un conjunto de imágenes editadas por el usuario en el frontend, las comprime en un único archivo ZIP estructurado y limpia físicamente todos los archivos asociados en el servidor.
- **Payload (Body - JSON):**
  ```json
  {
    "batch": [
      {
        "imageId": 1,
        "results": { ... }
      },
      {
        "imageId": 2,
        "results": { ... }
      }
    ]
  }
  ```
- **Respuesta (200 OK):**
  - Retorna un archivo binario ZIP: `Dataset_Lote_<cantidad>_Imagenes.zip`

### D. Eliminar Imagen

- **URL:** `/api/analysis/pose/image/<int:image_id>/`
- **Método:** `DELETE`
- **Descripción:** Destruye físicamente la imagen original, procesada, el JSON de reportes y el registro de base de datos asociado.

### E. Listar Archivos Locales del Servidor

- **URL:** `/api/analysis/pose/local-files/`
- **Método:** `POST`
- **Descripción:** Lista los archivos de imagen existentes dentro del subdirectorio "Imagen" de la ruta especificada en el servidor.
- **Payload (Body - JSON):**
  ```json
  {
    "target_path": "D:/mi_proyecto/dataset"
  }
  ```
- **Respuesta (200 OK):**
  ```json
  [
    { "id": "0001.jpg", "name": "0001.jpg" },
    { "id": "0002.jpg", "name": "0002.jpg" }
  ]
  ```

### F. Obtener Imagen Local y JSON Del Video

- **URL:** `/api/analysis/pose/local-file-data/`
- **Método:** `POST`
- **Descripción:** Convierte una imagen local a Base64 y extrae sus keypoints del JSON correspondiente. Maneja tanto imágenes estáticas como fotogramas específicos de video (`_frame_`).
- **Payload (Body - JSON):**
  ```json
  {
    "target_path": "D:/mi_proyecto/dataset",
    "file_name": "0001.jpg"
  }
  ```
- **Respuesta (200 OK):**
  ```json
  {
    "image_b64": "data:image/jpeg;base64,...",
    "json_data": {
      "model_used": "yolov8s-pose",
      "persons_detected": 1,
      "persons": [...]
    }
  }
  ```

---

## 10. API de Procesamiento y Clasificación de Video (Behavior)

Implementada en [behavior/views.py](/Biopose_BackEnd/backend/apps/analysis/api/behavior/views.py) y enrutada en [behavior/urls.py](/Biopose_BackEnd/backend/apps/analysis/api/behavior/urls.py).

### A. Iniciar Procesamiento de Video (Asíncrono)

- **URL:** `/api/analysis/videos/<int:video_id>/process/`
- **Método:** `POST`
- **Descripción:** Envía una tarea asíncrona a Celery para que procese el video de forma exhaustiva con YOLO (Detección de Pose) y el clasificador LSTM (Detección de Violencia/Disturbios/Hurtos/Normal).
- **Payload (Body - JSON - Opcionales):**
  - `mode` (String): `'operativo'` (default) | `'analitico'` | `'debug'`.
  - `dimension` (String): `'2D'` (default) | `'3D'`.
  - `fps_skip` (Integer): Fotogramas a saltar para optimizar procesamiento (default: `5`).
  - `confidence_threshold` (Float): Umbral mínimo de detección (default: `0.75`).
  - `analysis_type` (String): `'multipersona'` (default) | `'individual'`.
- **Ejemplo de payload (Body - JSON):**
  ```json
  {
    "mode": "operativo",
    "dimension": "2D",
    "fps_skip": 5,
    "confidence_threshold": 0.8,
    "analysis_type": "multipersona"
  }
  ```
- **Respuesta (202 Accepted):**
  ```json
  {
    "id": 10,
    "status": "processing",
    "task_id": "9a12b3c4-e8f9-40ab-bc11-a83d65b128fd",
    "message": "Video en procesamiento asíncrono. Puedes consultar progreso luego."
  }
  ```

### B. Obtener Resultados del Reporte de Video

- **URL:** `/api/analysis/videos/<int:video_id>/results/`
- **Método:** `GET`
- **Descripción:** Devuelve el resumen estadístico e información general del análisis del video una vez completado.
- **Respuestas:**
  - **202 Accepted (Aún procesando):**
    ```json
    {
      "id": 10,
      "status": "processing",
      "message": "El procesamiento aún está en curso."
    }
    ```
  - **200 OK (Completado):**
    ```json
    {
      "id": 10,
      "status": "completed",
      "total_frames": 300,
      "duration_seconds": 10.0,
      "processing_time_seconds": 3.45,
      "ruta_json_keypoints": "reports/keypoints_video_10.json",
      "analysis_report": {
        "total_detections": 2,
        "detections_by_type": { "PELEAR": 1, "DISTURBIO": 0 },
        "average_confidence": 0.88
      }
    }
    ```

### C. Obtener JSON Completo de Keypoints del Video

- **URL:** `/api/analysis/videos/<int:video_id>/keypoints-json/`
- **Método:** `GET`
- **Descripción:** Retorna el contenido completo del archivo JSON con los keypoints obtenidos fotograma por fotograma para propósitos de renderizado en el Frontend.
- **Respuesta (200 OK):**
  ```json
  {
    "id": 10,
    "status": "completed",
    "report_id": 5,
    "ruta_json_keypoints": "reports/keypoints_video_10.json",
    "keypoints": {
      "frames": [
        {
          "frame_index": 0,
          "timestamp_sec": 0.0,
          "keypoints_json": [...]
        }
      ],
      "detections": [...]
    }
  }
  ```

### D. Descargar Dataset de Video y Extraer Fotogramas en Caliente

- **URL:** `/api/analysis/videos/<int:video_id>/save-to-disk/`
- **Método:** `POST`
- **Descripción:** Genera un archivo ZIP descargable que contiene el JSON de keypoints y los fotogramas del video extraídos _al vuelo_ desde la RAM sin tocar disco del servidor (usando OpenCV en buffer). Posterior a esto, limpia físicamente el video, JSONs y base de datos.
- **Payload (Body - JSON):**
  - `results` (Object): JSON de keypoints modificado por el frontend.
  - `width` (Integer - Opcional): Ancho para redimensionar los fotogramas guardados.
  - `height` (Integer - Opcional): Alto para redimensionar los fotogramas guardados.
  ```json
  {
    "results": {},
    "width": 1280,
    "height": 720
  }
  ```
- **Respuesta (200 OK):**
  - Retorna un archivo binario ZIP: `Dataset_VideoFrames.zip`

---

## 11. API de Detección en Tiempo Real (Live - SSE & WebSockets)

Implementada en [live/views.py](/Biopose_BackEnd/backend/apps/analysis/api/live/views.py) (para SSE) y [live/consumers.py](/Biopose_BackEnd/backend/apps/analysis/api/live/consumers.py) (para WebSockets).

### A. Stream en Vivo vía Server-Sent Events (SSE)

- **Endpoint SSE (Individual):** `/api/analysis/live/stream/`
- **Endpoint SSE (Multipersona):** `/api/analysis/live/stream-multiperson/`
- **Método:** `GET`
- **Query Parameters:**
  - `fps_skip` (Integer): default `3`.
  - `dimension` (String): `'2D'` | `'3D'`.
  - `source` (String): `'local'` (Webcam del servidor) | `'remote'` (Cámara remota).
  - `url` (String): URL RTSP o HTTP si `source=remote`.
  - `mode` (String - Solo en multipersona): `'operativo'` | `'analitico'` | `'debug'`.
- **Descripción:** Mantiene una conexión HTTP abierta transmitiendo los frames decodificados en Base64 junto a las detecciones de pose y actitudes sospechosas en tiempo real mediante formato SSE (`data: ...`).

### B. Canales WebSocket (Detección Interactiva)

Enrutados en [live/routing.py](/Biopose_BackEnd/backend/apps/analysis/api/live/routing.py).

#### 1. Detección Individual

- **Path:** `ws/live-detection/`
- **Descripción:** El cliente (navegador) transmite periódicamente fotogramas capturados localmente codificados en Base64, y el backend responde con los keypoints y la imagen procesada.
- **Formato del mensaje enviado (Client -> Server):**
  ```json
  {
    "frame": "iVBORw0KGgoAAAANS...", // Base64 de la imagen
    "fps_skip": 3,
    "mode": "2D"
  }
  ```
- **Formato del mensaje recibido (Server -> Client):**
  ```json
  {
    "type": "result",
    "frame": "data:image/jpeg;base64,...",
    "detections": [...],
    "num_people": 1,
    "realtime_behaviors": ["NORMAL"],
    "total_detections": 12
  }
  ```

#### 2. Detección Multipersona

- **Path:** `ws/live-action-multiperson/`
- **Descripción:** Variante del WebSocket diseñada para detectar actitudes sospechosas en múltiples personas interactuando concurrentemente dentro del mismo encuadre.
- **Formato del mensaje enviado (Client -> Server):**
  ```json
  {
    "frame": "...",
    "fps_skip": 3,
    "mode": "2D",
    "visual_mode": "Modo Analítico (Esqueletos)" // 'operativo' | 'analitico' | 'debug'
  }
  ```
- **Formato del mensaje recibido (Server -> Client):**
  _(Idéntica estructura con soporte para múltiples bounding boxes y esqueletos estructurados)._

---

## 12. Tareas en Segundo Plano (Celery Tasks)

Definidas en [tasks.py](/Biopose_BackEnd/backend/apps/analysis/tasks.py).

### A. `process_video_task`

- **Uso:** Procesamiento de video asíncrono y clasificación LSTM.
- **Funcionamiento:**
  1. Cambia el estado del video en BD a `PROCESSING`.
  2. Invoca el motor de procesamiento (individual o multipersona).
  3. Escribe los keypoints en un archivo JSON físico temporal en `media/reports/keypoints_video_<id>.json`.
  4. Registra los resultados detallados en el modelo `AnalysisReport` (BD).
  5. Actualiza el estado del video a `COMPLETED` o `FAILED` en caso de error.

### B. `cleanup_orphaned_media_task`

- **Uso:** Tarea pasiva y periódica para liberar recursos en el disco de AWS.
- **Funcionamiento:**
  1. Escanea archivos de `VideoUpload` e `ImageUpload` con fecha de creación mayor a **1 hora**.
  2. Borra los archivos multimedia originales e intermedios del disco local/servidor.
  3. Elimina los reportes JSON físicos generados de la carpeta `media/reports/`.
  4. Remueve los registros obsoletos correspondientes de la base de datos.
