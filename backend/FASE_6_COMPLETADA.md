# FASE 6: MIGRACIÓN DE AUTENTICACION, USUARIOS, EMPRESAS Y ROLES (COMPLETADA)

## Objetivo
Migrar el sistema de login, permisos y estructura multi-inquilino (tenant) del legado Flask al nuevo backend en Django. Se establece un modelo donde una instancia puede soportar múltiples Empresas con roles personalizables e independientes.

## Tareas Realizadas

1. **Creación de los Endpoints de Autenticación (`apps/authentication`)**:
   - **Login**: Autenticación segura vía JWT.
   - **Manejo de Sesión**: Inclusión de llaves codificadas base SHA256 (compatibilidad Flask) expuestas en `/api/auth/login/`

2. **Endpoints de Gestión de Usuarios (`apps/users`)**:
   - **Registro (Creación de Cuenta)** en `/api/users/`.
   - **CRUD base**: Borrado lógico nativo protegido bajo JWT.

3. **Arquitectura Multi-Tenant (Empresas y Roles)** en `apps/gestionEmpresas`:
   - Extracción de la lógica de negocio a un dominio `Empresa`.
   - **Roles Dinámicos y Específicos por Empresa**: La tabla `rol` fue alterada (`idEmpresa` FK). Ahora los roles no son globales obligatoriamente; cada empresa tiene los suyos.
   - **Asignación Genérica Automática**: Se modificaron los endpoints (`asignarEmpresa`) para que si un usuario estándar ingresa mediante el `codigoEmpresa`, por defecto adquiera el rol `Invitado` instanciado para esa empresa.
   - Las validaciones internas ahora consultan a la tabla puente `EmpresaUsuarioRol` identificando siempre cuando alguien actúa como `"Administrador"` antes de modificar Empresa o crear/modificar Roles corporativos.

4. **Refactor de Estructura de Respuesta**:
   - Para homogeneizar con la UI, todo output adopta la notación paramétrica universal `{ codigo, mensaje, detalle }`.

5. **Auditoría Estandarizada por ID de Usuario**:
   - En todo el sistema, los campos `usuarioCreacion` y `usuarioModificacion` han pasado a registrarse utilizando el identificador numérico único del usuario (`idUsuario`), sustituyendo aproximaciones pasadas (como registrar el correo electrónico). Si el proceso no dispone de contexto de usuario, se identifica como `'Sistema'`.

## Endpoints Configurados para Uso (detalle por módulo)

A continuación se listan los endpoints y métodos implementados en esta fase, agrupados por aplicación.

### Authentication (`apps/authentication`)
- `POST /api/auth/login/` : Iniciar sesión (payload: `correo`, `password`) — retorna JWT.
- `POST /api/auth/registerAccount/` : Registro de cuenta (crea `Users`, valida correo/cedula).
- `POST /api/auth/verifyCedula/` : Verificar existencia de `cedula`.
- `POST /api/auth/verifyEmail/` : Verificar existencia de `correo`.

### Users (`apps/users`)
- `GET /api/users/` : Listar usuarios (filtros opcionales por `empresa_id` y `rol_id`).
- `GET /api/users/{idUsuario}/` : Obtener usuario por `idUsuario`.
- `GET /api/users/cedula/{cedula}/` : Obtener usuario por `cedula`.
- `PUT/PATCH /api/users/actualizarPorCedula/{cedula}/` : Actualizar usuario por `cedula` (ruta en camelCase: `actualizarPorCedula`).
- `DELETE /api/users/eliminar/{cedula}/` : Borrado lógico por `cedula` (estado → 'N').

### GestionEmpresas (`apps/gestionEmpresas`)
Empresa
- `GET /api/gestionEmpresas/empresas/` : Listar empresas activas.
- `POST /api/gestionEmpresas/empresas/` : Crear empresa — el creador se convierte en `Administrador` y se crean roles por defecto (`Administrador`, `Invitado`).
- `PUT/PATCH /api/gestionEmpresas/empresas/{codigoEmpresa}/` : Editar empresa (solo Administradores de la empresa).
- `POST /api/gestionEmpresas/empresas/asignarEmpresa/` : Asignarse a una empresa por `codigoEmpresa` + `cedula` (usa rol `Invitado` por defecto).

Roles
- `GET /api/gestionEmpresas/roles/` : Listar roles de la empresa del administrador autenticado.
- `POST /api/gestionEmpresas/roles/` : Crear rol (solo Administradores de la empresa).
- `PUT/PATCH /api/gestionEmpresas/roles/{id}/` : Editar rol (solo Administradores).
- `DELETE /api/gestionEmpresas/roles/{id}/` : Inhabilitar rol (estado = 'I').

EmpresaUsuarioRol (asignaciones)
- `POST /api/gestionEmpresas/asignarUsuarioRol/` : Asignar rol a usuario. Payload preferido: `{ "idUsuario": <int>, "idRol": <int> }`. También se acepta `{ "cedula": "...", "idRol": <int> }` o `rolId` como alias. Solo Administradores de la empresa pueden ejecutar.
- Al crear, si el usuario ya tiene una asignación activa en la empresa la petición será rechazada con un mensaje claro indicando el `idEmpresaUsuarioRol` existente y una sugerencia de uso.
- `PUT/PATCH /api/gestionEmpresas/asignarUsuarioRol/reasignar/` : Reasignar rol a un usuario. Payload: `{ "idUsuario": <int>, "idRol": <int> }`. Si existe una asignación activa para el usuario en la empresa del administrador, se inhabilitará la anterior y se creará la nueva asignación (retorna `201 Created`). Si no existe asignación activa, la petición retornará `404` indicando usar `POST`.
- `PUT /api/gestionEmpresas/asignarUsuarioRol/eliminar/` : Eliminar (quitar) rol al usuario por payload. Payload: `{ "idUsuario": <int> }` o `{ "cedula": "..." }`. Establece el rol en `NULL` de las asignaciones activas del usuario en las empresas donde el solicitante sea Administrador.


### MenuOpciones (`apps/menuOpciones`)
MenuOpcion
- `GET /api/menuOpciones/opciones/` : Listar opciones de menú activas (`estado='A'`).
- `GET /api/menuOpciones/opciones/usuario/{idUsuario}/` : Obtener opciones a las que un usuario tiene acceso (combina `EmpresaUsuarioRol` + `RolOption`).

RolOption (asignación Rol↔Opción)
- `POST /api/menuOpciones/asignarRolOpcion/` : Asignar una o varias opciones a un rol. Payload flexible: `{ "idRol": 1, "idOption": 2 }` o `{ "idRol":1, "idOptions": [2,3] }`. Reactiva relaciones inactivas si existen.
- `POST /api/menuOpciones/asignarRolOpcion/desasignar/` : Desasigna (inhabilita) una opción de un rol cambiando su estado a 'I'. Payload: `{ "idRol": <int>, "idOption": <int> }`. Solo Administradores de la empresa del rol pueden ejecutar.

***

## Criterio de Éxito Cumplido
✅ Migración de arquitectura multi-inquilino finalizada protegiendo la visibilidad y creación según el nivel Administrativo de la empresa.
✅ Control de endpoints con JWT y formatos en Notación Camel Case y estándares uniformes de JSON.

