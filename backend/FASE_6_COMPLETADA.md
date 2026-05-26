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

## Endpoints Configurados para Uso

A continuación se listan los endpoints principales habilitados en esta fase:

### 1. Iniciar Sesión (Login)
- **Ruta**: `POST /api/auth/login/`
- **Permisos**: Público

### 2. Gestión de Empresas y Miembros (Multi-empresa)
- **Crear Empresa** `POST /api/gestionEmpresas/empresas/`: (Registra empresa e inviste al creador como Administrador base).
- **Asignarse a una Empresa** `POST /api/gestionEmpresas/empresas/asignarEmpresa/`: (Usuario se ancla sin rol administrativo por default o como 'Invitado' si se inicializó).
- **Listar/Editar Empresa** `/api/gestionEmpresas/empresas/...`: Limitado a usuarios que contengan un registro `EmpresaUsuarioRol` como Administrador vigente.

### 3. Gestión y Personalización de Roles
- **Rutas CRUD Roles**: `/api/gestionEmpresas/roles/`
- Exclusivo para miembros que sean Administradores en la empresa. Útil para delegar o segmentar responsabilidades (ej. Rol "Supervisor de Cámaras"). Solo se retornan y modifican los de su propia empresa base. Permite borrado lógico ('A' activo, 'I' inactivo).

### 4. Asignación y Reasignación de Roles a Usuarios
- **Rutas CRUD Asignar Roles**: `POST /api/gestionEmpresas/asignarUsuarioRol/` (O `PUT/DELETE` mediante `/asignarUsuarioRol/{id}/`)
- **Payload Permisible (Flexible)**:
```json
{
    "cedula": "0987654321",
    "idRol": 7
}
```
*(No es necesario enviar `idEmpresa`; el backend lo auto-detecta basándose en la sesión del Administrador. Además, acepta `cedula` en lugar del ID numérico de usuario, e `idRol` o `rolId` indistintamente).*
- Protegido para uso exclusivo de **Administradores**. Permite actualizarle el rol a los usuarios preexistentes en la empresa (ej. promover de "Invitado" a otro rol customizado) y también eliminar su permanencia de la empresa (borrado lógico de la asociación `EmpresaUsuarioRol`).

***

## Criterio de Éxito Cumplido
✅ Migración de arquitectura multi-inquilino finalizada protegiendo la visibilidad y creación según el nivel Administrativo de la empresa.
✅ Control de endpoints con JWT y formatos en Notación Camel Case y estándares uniformes de JSON.

