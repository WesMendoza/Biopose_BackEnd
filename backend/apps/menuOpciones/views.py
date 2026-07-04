from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.views import APIView  # <--- 1. AGREGA ESTA LÍNEA AQUÍ
from django.db import transaction

from apps.gestionEmpresas.views import BaseStandardViewSet
from apps.gestionEmpresas.models import EmpresaUsuarioRol

# 2. AGREGA PathDirectory y SystemConfig A ESTA LÍNEA QUE YA TENÍAS:
from .models import MenuOpcion, RolOption, ParametroCabecera, ParametroDetalle

from .serializers import MenuOpcionSerializer, RolOptionSerializer

class MenuOpcionViewSet(BaseStandardViewSet):
    """
    CRUD para gestionar las Opciones del Menú (Rutas) Genericas.
    Las opciones son globales para todo el sistema.
    """
    serializer_class = MenuOpcionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        """
        Retorna TODAS las opciones de menú habilitadas (son genéricas).
        """
        return MenuOpcion.objects.filter(estado='A')

    @action(detail=False, methods=['get'], url_path=r'usuario/(?P<idUsuario>[^/.]+)')
    def opciones_por_usuario(self, request, idUsuario=None):
        """
        [GET] /api/menuOpciones/opciones/usuario/<idUsuario>/
        Retorna las opciones de menú a las que el usuario especificado
        tiene acceso, combinando información de RolOption y MenuOption.
        """
        # 1. Obtener los IDs de los roles que tiene el usuario indicado
        user_roles = EmpresaUsuarioRol.objects.filter(
            idUsuario=idUsuario, estado='A'
        ).values_list('idRol', flat=True)

        # 2. Obtener los RolOption permitidos para esos roles
        rol_opciones = RolOption.objects.filter(
            idRol__in=user_roles,
            estado='A',
            idOption__estado='A'
        ).select_related('idOption')

        # 3. Formatear la respuesta (rutas y opciones de rolOption + menuOption)
        detalle = []
        for ro in rol_opciones:
            detalle.append({
                "idRolOption": ro.idRolOption,
                "idRol": ro.idRol_id,
                "idOption": ro.idOption.idOption,
                "nombreOption": ro.idOption.nombreOption,
                "ruta": ro.idOption.ruta,
                "estado": ro.idOption.estado
            })

        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": f"Opciones de menú del usuario {idUsuario} obtenidas exitosamente.",
            "detalle": detalle
        }, status=status.HTTP_200_OK)


class RolOptionViewSet(BaseStandardViewSet):
    """
    ViewSet para asignar o visualizar las opciones de menú habilitadas por Rol.
    """
    serializer_class = RolOptionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']

    def get_queryset(self):
        """
        Retorna las opciones asociadas a los roles de la empresa actual del usuario.
        """
        # Obtenemos las empresas del usuario
        user_empresas = EmpresaUsuarioRol.objects.filter(
            idUsuario=self.request.user, estado='A'
        ).values_list('idEmpresa', flat=True)
        return RolOption.objects.filter(idRol__idEmpresa__in=user_empresas, estado='A')

    def _es_administrador(self, empresa_id):
        return EmpresaUsuarioRol.objects.filter(
            idUsuario=self.request.user, idEmpresa_id=empresa_id, idRol__nombreRol='Administrador', estado='A'
        ).exists()

    def create(self, request, *args, **kwargs):
        """
        [POST] /api/menuOpciones/asignarRolOpcion/
        Asignar una o varias opciones de menú a un rol. Solo Administradores.
        Payload esperado:
        {
           "idRol": 1,
           "idOption": 2  # Para asignar una sola
        }
        o
        {
           "idRol": 1,
           "idOptions": [2, 3, 4] # Para asignar varias a la vez
        }
        """
        data = request.data
        idRol = data.get('idRol')
        
        if not idRol:
             return Response({
                "codigo": status.HTTP_400_BAD_REQUEST,
                "mensaje": "idRol es requerido",
                "detalle": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.gestionEmpresas.models import Rol
        try:
            rol = Rol.objects.get(idRol=idRol)
        except Rol.DoesNotExist:
             return Response({
                "codigo": status.HTTP_404_NOT_FOUND,
                "mensaje": "Rol no encontrado",
                "detalle": None
            }, status=status.HTTP_404_NOT_FOUND)

        if not self._es_administrador(rol.idEmpresa_id):
             return Response({
                "codigo": status.HTTP_403_FORBIDDEN,
                "mensaje": "Acceso restringido",
                "detalle": "Sólo puede asignar opciones a roles de empresas que administra."
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Determinar si se envió una sola opción o una lista
        opciones_a_asignar = []
        if 'idOptions' in data and isinstance(data['idOptions'], list):
            opciones_a_asignar = data['idOptions']
        elif 'idOption' in data:
            opciones_a_asignar = [data['idOption']]
        else:
            return Response({
                "codigo": status.HTTP_400_BAD_REQUEST,
                "mensaje": "Debe enviar 'idOption' o 'idOptions'.",
                "detalle": None
            }, status=status.HTTP_400_BAD_REQUEST)

        opciones_creadas = []
        opciones_omitidas = []
        usuario_actual = str(getattr(request.user, 'idUsuario', 'Sistema'))
        
        with transaction.atomic():
            for id_opcion in opciones_a_asignar:
                # Evitar duplicados revisando si ya existe
                existente = RolOption.objects.filter(idRol=idRol, idOption=id_opcion).first()
                if existente:
                    if existente.estado == 'I':
                        # Si estaba inactivo, lo reactivamos
                        existente.estado = 'A'
                        existente.usuarioModificacion = usuario_actual
                        existente.save()
                        opciones_creadas.append({
                            "idRolOption": existente.idRolOption,
                            "idRol": idRol,
                            "idOption": id_opcion
                        })
                    else:
                        # Si ya estaba activo, lo omitimos
                        opciones_omitidas.append(id_opcion)
                else:
                    # Si no existe, creamos la nueva relación
                    nueva_relacion = RolOption(
                        idRol=rol, 
                        idOption_id=id_opcion,
                        idEmpresa_id=rol.idEmpresa_id,
                        estado='A',
                        usuarioCreacion=usuario_actual
                    )
                    nueva_relacion.save()
                    opciones_creadas.append({
                        "idRolOption": nueva_relacion.idRolOption,
                        "idRol": idRol,
                        "idOption": id_opcion
                    })
                    
        return Response({
            "codigo": status.HTTP_201_CREATED if opciones_creadas else status.HTTP_200_OK,
            "mensaje": "Proceso de asignación completado.",
            "detalle": {
                "asignadas": opciones_creadas,
                "omitidasPorDuplicidad": opciones_omitidas
            }
        }, status=status.HTTP_201_CREATED if opciones_creadas else status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='desasignar')
    def desasignar(self, request):
        """
        [POST] /api/menuOpciones/asignarRolOpcion/desasignar/
        Desasigna (inhabilita) una opción de menú de un rol.
        Payload esperado:
        {
            "idRol": 1,
            "idOption": 2
        }
        Solo Administradores de la empresa del rol pueden ejecutar.
        """
        data = request.data
        idRol = data.get('idRol')
        idOption = data.get('idOption')

        if not idRol or not idOption:
            return Response({
                "codigo": status.HTTP_400_BAD_REQUEST,
                "mensaje": "idRol e idOption son requeridos",
                "detalle": None
            }, status=status.HTTP_400_BAD_REQUEST)

        from apps.gestionEmpresas.models import Rol
        try:
            rol = Rol.objects.get(idRol=idRol)
        except Rol.DoesNotExist:
            return Response({
                "codigo": status.HTTP_404_NOT_FOUND,
                "mensaje": "Rol no encontrado",
                "detalle": None
            }, status=status.HTTP_404_NOT_FOUND)

        if not self._es_administrador(rol.idEmpresa_id):
            return Response({
                "codigo": status.HTTP_403_FORBIDDEN,
                "mensaje": "Acceso restringido",
                "detalle": "Sólo puede desasignar opciones de roles de empresas que administra."
            }, status=status.HTTP_403_FORBIDDEN)

        usuario_actual = str(getattr(request.user, 'idUsuario', 'Sistema'))
        relacion = RolOption.objects.filter(idRol=rol, idOption_id=idOption, estado='A').first()
        if not relacion:
            return Response({
                "codigo": status.HTTP_404_NOT_FOUND,
                "mensaje": "Relación Rol-Option activa no encontrada",
                "detalle": None
            }, status=status.HTTP_404_NOT_FOUND)

        relacion.estado = 'I'
        relacion.usuarioModificacion = usuario_actual
        relacion.save()

        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Opción desasignada del rol exitosamente (estado = I).",
            "detalle": {
                "idRolOption": relacion.idRolOption,
                "idRol": idRol,
                "idOption": idOption
            }
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        [DELETE] /api/menuOpciones/asignarRolOpcion/{id}/
        Elimina de manera lógica la relación Rol-Opción (estado = 'I'). Solo Administradores.
        """
        instance = self.get_object()
        
        if not self._es_administrador(instance.idRol.idEmpresa_id):
            return Response({
                "codigo": status.HTTP_403_FORBIDDEN,
                "mensaje": "Acceso restringido",
                "detalle": "No tiene permisos para desasignar opciones en esta empresa."
            }, status=status.HTTP_403_FORBIDDEN)
            
        instance.estado = 'I'
        instance.usuarioModificacion = str(getattr(request.user, 'idUsuario', 'Sistema'))
        instance.save()
        
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Opción removida del rol exitosamente.",
            "detalle": None
        }, status=status.HTTP_200_OK)

class ConfiguracionRutasView(APIView):
    """
    Gestiona la configuración global del sistema por EMPRESA.
    """
    
    def get(self, request, *args, **kwargs):
        id_empresa = request.query_params.get('idEmpresa')
        if not id_empresa:
            return Response({"error": "Falta idEmpresa"}, status=400)

        # 1. Buscamos la cabecera por empresa
        cabecera = ParametroCabecera.objects.filter(idEmpresa=id_empresa).first()
        
        if not cabecera:
            return Response([]) # Devuelve [] si no hay cabecera, tu frontend lo entenderá

        # 2. Buscamos detalles asociados a esa cabecera
        detalles = ParametroDetalle.objects.filter(
            codigoParametro=cabecera, # Aquí usamos el objeto directo
            estado='A'
        )
    
        data = [{"codigo": det.nombreDetalle, "valor": det.valor} for det in detalles]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        codigo_detalle = request.data.get('codigo') 
        valor = request.data.get('valor') 
        id_empresa = request.data.get('idEmpresa') # NUEVO: Recibimos de a qué empresa pertenece
        usuario_actual = str(getattr(request.user, 'idUsuario', 'Sistema'))

        if not codigo_detalle or not valor or not id_empresa:
            return Response(
                {"error": "Faltan parámetros", "message": "El código, el valor y el idEmpresa son requeridos."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generamos el código único para esta empresa
        codigo_cabecera = f'CONF_SISTEMA_EMP_{id_empresa}'

        try:
            # 1. Crear o buscar la Cabecera exclusiva para esta empresa
            cabecera, _ = ParametroCabecera.objects.get_or_create(
                codigoParametro=codigo_cabecera,
                defaults={
                    'idEmpresa': id_empresa, # Asignamos la empresa en la BD
                    'nombreParametro': f'Configuración Global - Empresa {id_empresa}',
                    'usuarioCreacion': usuario_actual
                }
            )

            # 2. Guardar el Detalle atado a esa cabecera específica
            detalle, created = ParametroDetalle.objects.update_or_create(
                codigoParametro=cabecera,
                nombreDetalle=codigo_detalle,
                defaults={
                    'valor': valor,
                    'descripcion': f'Configuración {codigo_detalle} para Empresa {id_empresa}',
                    'usuarioModificacion': usuario_actual
                }
            )

            return Response({
                "success": True,
                "message": "Parámetro de empresa guardado exitosamente.",
                "codigo": codigo_detalle,
                "valor": valor,
                "idEmpresa": id_empresa
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": "Database Error", "message": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )