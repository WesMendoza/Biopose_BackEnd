from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db import transaction

from .models import Empresa, Rol, EmpresaUsuarioRol
from .serializers import (
    EmpresaSerializer, RolSerializer, 
    EmpresaUsuarioRolSerializer
)

class BaseStandardViewSet(viewsets.ModelViewSet):
    """
    ViewSet base para unificar las respuestas con el formato:
    { codigo, mensaje, detalle }
    """
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": f"Lista obtenida exitosamente",
            "detalle": serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": f"Registro obtenido exitosamente",
            "detalle": serializer.data
        })

    def perform_create(self, serializer):
        user_identifier = str(getattr(self.request.user, 'idUsuario', 'Sistema'))
        serializer.save(usuarioCreacion=user_identifier, usuarioModificacion=user_identifier)

    def perform_update(self, serializer):
        user_identifier = str(getattr(self.request.user, 'idUsuario', 'Sistema'))
        serializer.save(usuarioModificacion=user_identifier)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "codigo": status.HTTP_201_CREATED,
                "mensaje": "Registro creado exitosamente",
                "detalle": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "codigo": status.HTTP_400_BAD_REQUEST,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                "codigo": status.HTTP_200_OK,
                "mensaje": "Registro actualizado exitosamente",
                "detalle": serializer.data
            })
        return Response({
            "codigo": status.HTTP_400_BAD_REQUEST,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Registro eliminado exitosamente",
            "detalle": None
        }, status=status.HTTP_200_OK)


class EmpresaViewSet(BaseStandardViewSet):
    """
    Gestión de Empresas.
    """
    queryset = Empresa.objects.filter(estado='A')  # Solo obtener empresas activas
    serializer_class = EmpresaSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'codigoEmpresa'  # Usar codigoEmpresa en lugar del 'id' en las URLs

    def get_queryset(self):
        """
        Sobreescribe la consulta base para filtrar por la empresa del usuario
        si se recibe el parámetro 'idEmpresa'.
        Además, asegura que el usuario solo pueda ver las empresas a las que pertenece.
        """
        queryset = super().get_queryset()
        id_empresa_param = self.request.query_params.get('idEmpresa')

        # 1. Obtenemos las empresas a las que pertenece el usuario autenticado
        empresas_del_usuario = EmpresaUsuarioRol.objects.filter(
            idUsuario=self.request.user, 
            estado='A'
        ).values_list('idEmpresa', flat=True)

        # 2. Filtramos el queryset para que SOLO devuelva las empresas del usuario
        queryset = queryset.filter(idEmpresa__in=empresas_del_usuario)

        # 3. Si el frontend manda un idEmpresa específico (para asegurar concordancia)
        if id_empresa_param:
            queryset = queryset.filter(idEmpresa=id_empresa_param)

        return queryset

    def list(self, request, *args, **kwargs):
        """
        [GET] /api/gestionEmpresas/empresas/
        1. Consultar Empresas (Todas las activas vinculadas al usuario)
        """
        return super().list(request, *args, **kwargs)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        [POST] /api/gestionEmpresas/empresas/
        2. Crear empresa.
        Regla de negocio: El usuario que crea la empresa se convierte en el "Administrador" de la misma.
        Regla de negocio: Un usuario NO puede crear/tener más de 1 empresa asignada.
        Regla de negocio: El RUC de la empresa debe ser único.
        Regla de negocio: El código de empresa se genera automáticamente (ej. EMP001).
        """
        # Validar que el usuario NO tenga ya una empresa asignada (creada o unida)
        if EmpresaUsuarioRol.objects.filter(idUsuario=request.user, estado='A').exists():
            return Response({
                "codigo": status.HTTP_400_BAD_REQUEST,
                "mensaje": "El usuario ya pertenece o administra una empresa. No puede crear ni pertenecer a más de una.",
                "detalle": None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar que el RUC sea único
        ruc = request.data.get('ruc')
        if ruc and Empresa.objects.filter(ruc=ruc).exists():
            return Response({
                "codigo": status.HTTP_400_BAD_REQUEST,
                "mensaje": "Ya existe una empresa registrada con este RUC.",
                "detalle": None
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user_identifier = str(getattr(request.user, 'idUsuario', 'Sistema'))
            # Crear la empresa
            empresa = serializer.save(estado='A', usuarioCreacion=user_identifier, usuarioModificacion=user_identifier)
            
            # Generar el código de empresa basado en el ID y guardarlo
            empresa.codigoEmpresa = f"EMP{empresa.idEmpresa:03d}"
            empresa.save(update_fields=['codigoEmpresa'])
            
            # Crear roles genericos para esta empresa internamente
            rol_admin = Rol.objects.create(
                idEmpresa=empresa,
                nombreRol='Administrador',
                estado='A',
                usuarioCreacion=user_identifier,
                usuarioModificacion=user_identifier
            )
            
            Rol.objects.create(
                idEmpresa=empresa,
                nombreRol='Invitado',
                estado='A',
                usuarioCreacion=user_identifier,
                usuarioModificacion=user_identifier
            )

            # Asignar la empresa al usuario que la creó, con el rol de Administrador
            EmpresaUsuarioRol.objects.create(
                idEmpresa=empresa,
                idUsuario=request.user,
                idRol=rol_admin,
                estado='A',
                usuarioCreacion=user_identifier,
                usuarioModificacion=user_identifier
            )

            # Obtener datos con el código de empresa actualizado
            datos_actualizados = self.get_serializer(empresa).data

            return Response({
                "codigo": status.HTTP_201_CREATED,
                "mensaje": "Empresa creada exitosamente y asignada como Administrador.",
                "detalle": datos_actualizados
            }, status=status.HTTP_201_CREATED)
            
        return Response({
            "codigo": status.HTTP_400_BAD_REQUEST,
            "mensaje": "Error de validación al crear empresa",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # =========================================================================
    # metodo update con validación de rol 'Administrador' para editar la empresa
    # =========================================================================
    def update(self, request, *args, **kwargs):
        """
        [PUT/PATCH] /api/gestionEmpresas/empresas/{codigoEmpresa}/
        Editar Empresa por su código único. Restringido a rol 'Administrador'.
        """
        # get_object() ahora buscará automáticamente usando el campo 'codigoEmpresa'
        instance = self.get_object()
        
        # Validación de seguridad
        esAdmin = EmpresaUsuarioRol.objects.filter(
            idEmpresa=instance,
            idUsuario=request.user,
            idRol__nombreRol='Administrador',
            estado='A'
        ).exists()

        if not esAdmin:
            return Response({
                "codigo": status.HTTP_403_FORBIDDEN,
                "mensaje": "Acceso restringido",
                "detalle": "Solo los administradores de la empresa pueden modificar su información."
            }, status=status.HTTP_403_FORBIDDEN)

        # Ejecución estándar del update heredado
        response = super().update(request, *args, **kwargs)
        
        # Formateamos la respuesta exitosa bajo tu estándar de estructura
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Empresa actualizada exitosamente",
            "detalle": response.data
        }, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['post'], url_path='asignarEmpresa')
    def asignarEmpresa(self, request):
        """
        [POST] /api/gestionEmpresas/empresas/asignarEmpresa/
        3. Asignarse a una empresa mediante su código (codigoEmpresa) y la cédula del usuario (cedula).
        Regla de negocio: Un usuario NO puede tener más de 1 empresa asignada de forma activa (con rol asignado).
        Regla de negocio: El usuario ingresa sin rol (idRol=None).
        """
        codigoEmpresa = request.data.get('codigoEmpresa')
        cedula = request.data.get('cedula')

        if not codigoEmpresa or not cedula:
            return Response({
                "codigo": status.HTTP_400_BAD_REQUEST,
                "mensaje": "Debe proporcionar el 'codigoEmpresa' y la 'cedula'.",
                "detalle": None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si la empresa existe y está activa
        try:
            empresa = Empresa.objects.get(codigoEmpresa=codigoEmpresa, estado='A')
        except Empresa.DoesNotExist:
            return Response({
                "codigo": status.HTTP_404_NOT_FOUND,
                "mensaje": "Empresa no encontrada o inactiva.",
                "detalle": None
            }, status=status.HTTP_404_NOT_FOUND)

        # Buscar usuario por cedula
        try:
            from apps.users.models import Users
            usuarioSolicitante = Users.objects.get(cedula=cedula, estado='A')
        except Exception:
            return Response({
                "codigo": status.HTTP_404_NOT_FOUND,
                "mensaje": "Usuario no encontrado con esa cédula.",
                "detalle": None
            }, status=status.HTTP_404_NOT_FOUND)

        # Validar que el usuario NO tenga otra empresa asignada de forma activa (ignorando registros donde el idEmpresa sea Null)
        if EmpresaUsuarioRol.objects.filter(idUsuario=usuarioSolicitante, idEmpresa__isnull=False, estado='A').exists():
            return Response({
                "codigo": status.HTTP_400_BAD_REQUEST,
                "mensaje": "El usuario ya tiene una empresa asignada. No puede pertenecer a más de 1 empresa.",
                "detalle": None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Buscar el rol de "Invitado" particular de esta empresa
        try:
            rol_invitado = Rol.objects.get(idEmpresa=empresa, nombreRol='Invitado', estado='A')
        except Rol.DoesNotExist:
            rol_invitado = None

        # Asignar la empresa al usuario con el rol de Invitado
        user_identifier = str(getattr(request.user, 'idUsuario', 'Sistema'))
        EmpresaUsuarioRol.objects.create(
            idEmpresa=empresa,
            idUsuario=usuarioSolicitante,
            idRol=rol_invitado,
            estado='A',
            usuarioCreacion=user_identifier,
            usuarioModificacion=user_identifier
        )

        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": f"El usuario se ha unido exitosamente a la empresa '{empresa.nombreEmpresa}' con el rol de Invitado.",
            "detalle": None
        }, status=status.HTTP_200_OK)


class RolViewSet(BaseStandardViewSet):
    """
    Gestión de Roles asociados a cada Empresa.
    """
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna sólo los roles de la empresa a la que pertenece el usuario administrador.
        """
        user_empresas = EmpresaUsuarioRol.objects.filter(
            idUsuario=self.request.user, estado='A', idRol__nombreRol='Administrador'
        ).values_list('idEmpresa', flat=True)
        return Rol.objects.filter(estado='A', idEmpresa__in=user_empresas)

    def _es_administrador(self, empresa_id):
        return EmpresaUsuarioRol.objects.filter(
            idUsuario=self.request.user, idEmpresa_id=empresa_id, idRol__nombreRol='Administrador', estado='A'
        ).exists()

    def list(self, request, *args, **kwargs):
        """
        [GET] /api/gestionEmpresas/roles/
        Consultar Roles habilitados para la empresa del administrador logueado.
        """
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        [POST] /api/gestionEmpresas/roles/
        Crear Rol (solo administradores pueden crear en su respectiva empresa)
        """
        import copy
        
        # Permitir modificación de parámetros de entrada
        try:
            data = request.data.copy()
        except AttributeError:
            data = copy.deepcopy(request.data)
            
        idEmpresa = data.get('idEmpresa')

        # Auto-detectar de qué empresa es administrador si no lo provee
        if not idEmpresa:
            admin_record = EmpresaUsuarioRol.objects.filter(
                idUsuario=request.user, 
                idRol__nombreRol='Administrador', 
                estado='A'
            ).first()
            if admin_record:
                idEmpresa = admin_record.idEmpresa_id
                data['idEmpresa'] = idEmpresa

        if not idEmpresa or not self._es_administrador(idEmpresa):
             return Response({
                "codigo": status.HTTP_403_FORBIDDEN,
                "mensaje": "Acceso restringido",
                "detalle": "Sólo puede crear roles en las empresas que administra."
            }, status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "codigo": status.HTTP_201_CREATED,
                "mensaje": "Registro creado exitosamente",
                "detalle": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        return Response({
            "codigo": status.HTTP_400_BAD_REQUEST,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        [PUT/PATCH] /api/gestionEmpresas/roles/{id}/
        Editar Rol (solo administrador de la empresa dueña del rol)
        """
        rol = self.get_object()
        if not self._es_administrador(rol.idEmpresa_id):
             return Response({
                "codigo": status.HTTP_403_FORBIDDEN,
                "mensaje": "Acceso restringido",
                "detalle": "No tiene permisos para editar este rol."
            }, status=status.HTTP_403_FORBIDDEN)
             
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        [DELETE] /api/gestionEmpresas/roles/{id}/
        Eliminar lógicamente rol (Cambia estado a 'I' en vez de 'N' para ser consistente con el estatus del modelo general).
        Sólo por el administrador.
        """
        rol = self.get_object()
        if not self._es_administrador(rol.idEmpresa_id):
             return Response({
                "codigo": status.HTTP_403_FORBIDDEN,
                "mensaje": "Acceso restringido",
                "detalle": "No tiene permisos para eliminar este rol."
            }, status=status.HTTP_403_FORBIDDEN)

        rol.estado = 'I'
        rol.usuarioModificacion = str(getattr(request.user, 'idUsuario', 'Sistema'))
        rol.save()
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Rol inhabilitado exitosamente (estado = I).",
            "detalle": None
        }, status=status.HTTP_200_OK)

class EmpresaUsuarioRolViewSet(BaseStandardViewSet):
    """ 
    ViewSet para 'asignar' y gestionar la relación Empresa-Usuario-Rol 
    """
    serializer_class = EmpresaUsuarioRolSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Solo permite consultar asignaciones de la empresa donde el usuario es Administrador.
        """
        user_empresas = EmpresaUsuarioRol.objects.filter(
            idUsuario=self.request.user, estado='A', idRol__nombreRol='Administrador'
        ).values_list('idEmpresa', flat=True)
        return EmpresaUsuarioRol.objects.filter(estado='A', idEmpresa__in=user_empresas)

    def _es_administrador(self, empresa_id):
        return EmpresaUsuarioRol.objects.filter(
            idUsuario=self.request.user, idEmpresa_id=empresa_id, idRol__nombreRol='Administrador', estado='A'
        ).exists()

    def create(self, request, *args, **kwargs):
        """
        [POST] /api/gestionEmpresas/asignarUsuarioRol/
        2. Asignar rol a usuario que tiene su empresa.
        (Puede recibir idUsuario o cedula, idRol o rolId, e idEmpresa opcional)
        Solo permitdo para Administradores de la empresa
        """
        import copy
        
        try:
            data = request.data.copy()
        except AttributeError:
            data = copy.deepcopy(request.data)
            
        id_empresa = data.get('idEmpresa')
        id_usuario = data.get('idUsuario')
        cedula = data.get('cedula')
        id_rol = data.get('idRol') or data.get('rolId')
        
        # Auto-detectar de qué empresa es administrador si no lo provee
        if not id_empresa:
            admin_record = EmpresaUsuarioRol.objects.filter(
                idUsuario=request.user, 
                idRol__nombreRol='Administrador', 
                estado='A'
            ).first()
            if admin_record:
                id_empresa = admin_record.idEmpresa_id
                data['idEmpresa'] = id_empresa

        # Validar permisos de administrador en la empresa destino
        if not id_empresa or not self._es_administrador(id_empresa):
            return Response({
                "codigo": status.HTTP_403_FORBIDDEN,
                "mensaje": "Acceso restringido",
                "detalle": "Sólo un Administrador de la empresa puede reasignar roles de sus usuarios."
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Si se envía cédula en vez de idUsuario, buscar el usuario
        if not id_usuario and cedula:
            try:
                from apps.users.models import Users
                user_obj = Users.objects.get(cedula=cedula, estado='A')
                id_usuario = user_obj.idUsuario
                data['idUsuario'] = id_usuario
            except Exception:
                return Response({
                    "codigo": status.HTTP_404_NOT_FOUND,
                    "mensaje": "Usuario no encontrado",
                    "detalle": "No existe un usuario activo con la cédula proporcionada."
                }, status=status.HTTP_404_NOT_FOUND)
                
        # Asegurarnos de que el idRol se mapee correctamente para el serializer
        if id_rol:
            if not Rol.objects.filter(idRol=id_rol, estado='A').exists():
                return Response({
                    "codigo": status.HTTP_400_BAD_REQUEST,
                    "mensaje": "El rol a asignar no existe o se encuentra inactivo.",
                    "detalle": None
                }, status=status.HTTP_400_BAD_REQUEST)
            data['idRol'] = id_rol

        # Lógica para evitar duplicados si el usuario ya se unió a la empresa usando "asignarse_por_codigo"
        if id_usuario and id_empresa:
            asignacion = EmpresaUsuarioRol.objects.filter(
                idUsuario=id_usuario, 
                idEmpresa=id_empresa, 
                estado='A'
            ).first()
            
            if asignacion:
                if asignacion.idRol_id is not None:
                    # Si ya existe una asignación activa y tiene rol, rechazamos la creación.
                    return Response({
                        "codigo": status.HTTP_400_BAD_REQUEST,
                        "mensaje": "El usuario ya tiene un rol asignado en esta empresa.",
                        "detalle": {
                            "idEmpresaUsuarioRol": asignacion.idEmpresaUsuarioRol,
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Si la asignación existe pero tiene el rol en NULL, le asignamos el nuevo rol
                    asignacion.idRol_id = id_rol
                    asignacion.usuarioModificacion = str(getattr(request.user, 'idUsuario', 'Sistema'))
                    asignacion.save()
                    
                    serializer = self.get_serializer(asignacion)
                    return Response({
                        "codigo": status.HTTP_201_CREATED,
                        "mensaje": "Rol asignado exitosamente al usuario (asignación previa actualizada).",
                        "detalle": serializer.data
                    }, status=status.HTTP_201_CREATED)

        # Si no existe asignación previa (creación manual completa), ejecuta la normal
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "codigo": status.HTTP_201_CREATED,
                "mensaje": "Registro creado exitosamente",
                "detalle": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        return Response({
            "codigo": status.HTTP_400_BAD_REQUEST,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put', 'patch'], url_path='reasignar')
    def reasignar_por_payload(self, request):
        """
        [PUT/PATCH] /api/gestionEmpresas/asignarUsuarioRol/reasignar/
        Reasigna un rol a un usuario usando payload { idUsuario, idRol }.
        """
        try:
            data = request.data.copy()
        except Exception:
            data = request.data

        id_usuario = data.get('idUsuario')
        id_rol = data.get('idRol') or data.get('rolId')

        if not id_usuario or not id_rol:
            return Response({
                "codigo": status.HTTP_400_BAD_REQUEST,
                "mensaje": "Se requieren 'idUsuario' y 'idRol' en el payload.",
                "detalle": None
            }, status=status.HTTP_400_BAD_REQUEST)

        if not Rol.objects.filter(idRol=id_rol, estado='A').exists():
            return Response({
                "codigo": status.HTTP_400_BAD_REQUEST,
                "mensaje": "El rol a asignar no existe o se encuentra inactivo.",
                "detalle": None
            }, status=status.HTTP_400_BAD_REQUEST)

        asignacion = EmpresaUsuarioRol.objects.filter(idUsuario=id_usuario, estado='A').first()
        if not asignacion:
            return Response({
                "codigo": status.HTTP_404_NOT_FOUND,
                "mensaje": "No se encontró una asignación activa para el usuario. Use POST para crear una asignación.",
                "detalle": None
            }, status=status.HTTP_404_NOT_FOUND)

        if not self._es_administrador(asignacion.idEmpresa_id):
            return Response({
                "codigo": status.HTTP_403_FORBIDDEN,
                "mensaje": "Acceso restringido: solo Administradores pueden reasignar roles.",
                "detalle": None
            }, status=status.HTTP_403_FORBIDDEN)

        if int(asignacion.idRol_id) == int(id_rol):
            return Response({
                "codigo": status.HTTP_200_OK,
                "mensaje": "El usuario ya tiene el rol solicitado; no se realizaron cambios.",
                "detalle": {"idEmpresaUsuarioRol": asignacion.idEmpresaUsuarioRol}
            }, status=status.HTTP_200_OK)

        asignacion.estado = 'I'
        asignacion.usuarioModificacion = str(getattr(request.user, 'idUsuario', 'Sistema'))
        asignacion.save()

        user_identifier = str(getattr(request.user, 'idUsuario', 'Sistema'))
        nueva = EmpresaUsuarioRol.objects.create(
            idEmpresa=asignacion.idEmpresa,
            idUsuario=asignacion.idUsuario,
            idRol_id=id_rol,
            estado='A',
            usuarioCreacion=user_identifier,
            usuarioModificacion=user_identifier
        )

        serializer = self.get_serializer(nueva)
        return Response({
            "codigo": status.HTTP_201_CREATED,
            "mensaje": "Rol reasignado correctamente.",
            "detalle": serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put'], url_path='eliminar')
    def eliminar_por_usuario(self, request):
        """
        [PUT] /api/gestionEmpresas/asignarUsuarioRol/eliminar/
        Desasigna el rol (establece `idRol = NULL`) de la(s) asignación(es) activa(s) de un `idUsuario`.
        """
        try:
            data = request.data.copy()
        except Exception:
            data = request.data

        id_usuario = data.get('idUsuario')
        cedula = data.get('cedula')

        if not id_usuario and not cedula:
            return Response({
                "codigo": status.HTTP_400_BAD_REQUEST,
                "mensaje": "Se requiere 'idUsuario' o 'cedula' para eliminar asignaciones.",
                "detalle": None
            }, status=status.HTTP_400_BAD_REQUEST)

        if not id_usuario and cedula:
            try:
                from apps.users.models import Users
                user_obj = Users.objects.get(cedula=cedula, estado='A')
                id_usuario = user_obj.idUsuario
            except Exception:
                return Response({
                    "codigo": status.HTTP_404_NOT_FOUND,
                    "mensaje": "Usuario no encontrado con esa cédula.",
                    "detalle": None
                }, status=status.HTTP_404_NOT_FOUND)

        asignaciones = EmpresaUsuarioRol.objects.filter(idUsuario=id_usuario, estado='A')
        if not asignaciones.exists():
            return Response({
                "codigo": status.HTTP_404_NOT_FOUND,
                "mensaje": "No se encontraron asignaciones activas para el usuario.",
                "detalle": None
            }, status=status.HTTP_404_NOT_FOUND)

        empresas_afectadas = set(asignaciones.values_list('idEmpresa_id', flat=True))
        permitted = any(self._es_administrador(eid) for eid in empresas_afectadas)
        if not permitted:
            return Response({
                "codigo": status.HTTP_403_FORBIDDEN,
                "mensaje": "Acceso restringido: no eres Administrador de las empresas afectadas.",
                "detalle": None
            }, status=status.HTTP_403_FORBIDDEN)

        usuario_mod = str(getattr(request.user, 'idUsuario', 'Sistema'))
        # En lugar de inhabilitar la asignación, dejamos el rol en NULL (desasignar rol)
        updated = asignaciones.update(idRol=None, usuarioModificacion=usuario_mod)

        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": f"Se han desasignado el rol del usuario.",
            "detalle": {"idUsuario": id_usuario}
        }, status=status.HTTP_200_OK)