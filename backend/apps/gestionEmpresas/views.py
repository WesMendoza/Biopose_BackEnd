from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db import transaction

from .models import Empresa, Rol, Menuoption, EmpresaUsuarioRol, RolOption
from .serializers import (
    EmpresaSerializer, RolSerializer, MenuoptionSerializer, 
    EmpresaUsuarioRolSerializer, RolOptionSerializer
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

    def list(self, request, *args, **kwargs):
        """
        [GET] /api/gestionEmpresas/empresas/
        1. Consultar Empresas (Todas las activas)
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
            # Crear la empresa
            empresa = serializer.save(estado='A')
            
            # Generar el código de empresa basado en el ID y guardarlo
            empresa.codigoEmpresa = f"EMP{empresa.idEmpresa:03d}"
            empresa.save(update_fields=['codigoEmpresa'])
            
            # Buscar o crear el Rol de Administrador
            rol_admin, _ = Rol.objects.get_or_create(
                nombreRol='Administrador', 
                defaults={'estado': 'A'}
            )

            # Asignar la empresa al usuario que la creó, con el rol de Administrador
            EmpresaUsuarioRol.objects.create(
                idEmpresa=empresa,
                idUsuario=request.user,
                idRol=rol_admin,
                estado='A'
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

        # Asignar la empresa al usuario (dejamos el idRol en None, esperando que el Admin le asigne su rol más tarde)
        EmpresaUsuarioRol.objects.create(
            idEmpresa=empresa,
            idUsuario=usuarioSolicitante,
            idRol=None,
            estado='A'
        )

        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": f"El usuario se ha unido exitosamente a la empresa '{empresa.nombreEmpresa}'.",
            "detalle": None
        }, status=status.HTTP_200_OK)


class RolViewSet(BaseStandardViewSet):
    """
    Gestión de Roles (Para uso del Administrador).
    """
    queryset = Rol.objects.filter(estado='A')  # Solo listar roles activos
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """
        [GET] /gestion-empresas/rol/
        4. Consultar Rol (Obtiene lista de todos los roles activos)
        """
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        [POST] /gestion-empresas/rol/
        1. Crear Rol. 
        """
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        [PUT/PATCH] /gestion-empresas/rol/{id}/
        4. Editar Rol (Cambiar su nombre u otros atributos).
        """
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        [DELETE] /gestion-empresas/rol/{id}/
        4. Eliminar lógicamente rol (Cambia estado a 'I').
        """
        rol = self.get_object()
        rol.estado = 'I'
        rol.save()
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Rol eliminado exitosamente (borrado lógico a 'I').",
            "detalle": None
        }, status=status.HTTP_200_OK)


class MenuoptionViewSet(BaseStandardViewSet):
    queryset = Menuoption.objects.all()
    serializer_class = MenuoptionSerializer
    permission_classes = [IsAuthenticated]

class EmpresaUsuarioRolViewSet(BaseStandardViewSet):
    """ 
    ViewSet para 'asignar' y gestionar la relación Empresa-Usuario-Rol 
    """
    queryset = EmpresaUsuarioRol.objects.filter(estado='A')
    serializer_class = EmpresaUsuarioRolSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        [POST] /gestion-empresas/asignar-usuario-rol/
        2. Asignar rol a usuario que tiene su empresa.
        (Recibe idUsuario, idEmpresa, idRol)
        """
        id_usuario = request.data.get('idUsuario')
        id_empresa = request.data.get('idEmpresa')
        
        # Lógica para evitar duplicados si el usuario ya se unió a la empresa usando "asignarse_por_codigo"
        if id_usuario and id_empresa:
            asignacion = EmpresaUsuarioRol.objects.filter(
                idUsuario=id_usuario, 
                idEmpresa=id_empresa, 
                estado='A'
            ).first()
            
            if asignacion:
                # Actualiza la asignación existente en lugar de crear otra nueva
                serializer = self.get_serializer(asignacion, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        "codigo": status.HTTP_200_OK,
                        "mensaje": "Rol asignado/actualizado exitosamente al usuario en la empresa.",
                        "detalle": serializer.data
                    })
                return Response({
                    "codigo": status.HTTP_400_BAD_REQUEST,
                    "mensaje": "Error de validación",
                    "detalle": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        # Si no existe asignación previa (creación manual completa), ejecuta la normal
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        [DELETE] /gestion-empresas/asignar-usuario-rol/{id}/
        3. Eliminar lógicamente rol de la empresa.
        """
        instance = self.get_object()
        instance.estado = 'I'
        instance.save()
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Asignación de rol a empresa eliminada exitosamente (borrado lógico a 'I').",
            "detalle": None
        }, status=status.HTTP_200_OK)


class RolOptionViewSet(BaseStandardViewSet):
    """ ViewSet para 'asignar' y gestionar opciones de menú a los Roles """
    queryset = RolOption.objects.all()
    serializer_class = RolOptionSerializer
    permission_classes = [IsAuthenticated]
