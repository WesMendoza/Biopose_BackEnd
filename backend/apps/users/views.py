from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny 
from rest_framework.decorators import action
from apps.authentication.utils import hash_password
from django.db.models import F

from .models import Users
from .serializers import UsersSerializer

class UsersViewSet(viewsets.ModelViewSet):
    """
    Controlador (ViewSet) para operaciones CRUD sobre Users
    """
    queryset = Users.objects.filter(estado='A')  # Solo listar usuarios activos por defecto
    serializer_class = UsersSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    # =========================================================================
    # MÉTODOS BASE (OVERRIDE DE DEFAULT VIEWSET)
    # =========================================================================

    def get_queryset(self):
        """
        [GET] Obtiene la consulta base. Añade filtros opcionales por empresa y rol.
        """
        queryset = super().get_queryset()
        
        # Aceptamos tanto 'idEmpresa' (React) como 'empresa_id' (Legacy)
        empresa_id = self.request.query_params.get('idEmpresa') or self.request.query_params.get('empresa_id')
        rol_id = self.request.query_params.get('idRol') or self.request.query_params.get('rol_id')

        if empresa_id or rol_id:
            from apps.gestionEmpresas.models import EmpresaUsuarioRol
            filtros = {'estado': 'A'}
            if empresa_id:
                filtros['idEmpresa'] = empresa_id
            if rol_id:
                filtros['idRol'] = rol_id
            
            # Buscamos los IDs de usuarios que pertenecen a esta empresa / rol
            usuarios_validos = EmpresaUsuarioRol.objects.filter(**filtros).values_list('idUsuario', flat=True)
            queryset = queryset.filter(idUsuario__in=usuarios_validos)

            # MAGIA PARA EL FRONTEND: Anotamos el idRol y el nombreRol para que React no tenga que cruzarlos
            if empresa_id:
                queryset = queryset.annotate(
                    idRol_anotado=F('empresausuariorol__idRol'),
                    nombreRol_anotado=F('empresausuariorol__idRol__nombreRol') # Asumiendo que tu Foreign Key se llama idRol y apunta al modelo Rol que tiene 'nombreRol'
                )

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        """
        [GET] /users/
        Obtiene la lista de todos los usuarios (aplica filtros de get_queryset).
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # En lugar de usar el serializador estándar, armamos una respuesta enriquecida
        # para enviar los roles anotados si existen
        detalles = []
        for user in queryset:
            user_data = self.get_serializer(user).data
            # Si anotamos el rol, lo inyectamos en el JSON
            if hasattr(user, 'idRol_anotado'):
                user_data['idRol'] = user.idRol_anotado
                user_data['nombreRol'] = user.nombreRol_anotado
            detalles.append(user_data)

        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Lista de usuarios obtenida exitosamente",
            "detalle": detalles
        })

    def retrieve(self, request, *args, **kwargs):
        """
        [GET] /users/{idUsuario}/
        Obtiene el detalle de un usuario específico por su ID principal (PK).
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Usuario obtenido exitosamente",
            "detalle": serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        [POST] /users/
        Crea un nuevo usuario en el sistema.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            password_plana = serializer.validated_data.get('password')
            password_hasheada = hash_password(password_plana)
            user = serializer.save(password=password_hasheada)
            return Response({
                "codigo": status.HTTP_201_CREATED,
                "mensaje": "Usuario creado exitosamente",
                "detalle": self.get_serializer(user).data
            }, status=status.HTTP_201_CREATED)
            
        return Response({
            "codigo": status.HTTP_400_BAD_REQUEST,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # MÉTODOS PERSONALIZADOS (ACCIONES EXTRAS)
    # =========================================================================

    @action(detail=False, methods=['get'], url_path='cedula/(?P<cedula>[^/.]+)')
    def get_by_cedula(self, request, cedula=None):
        """
        [GET] /users/cedula/{cedula}/
        Obtener el detalle de un usuario específico buscando por su cédula.
        """
        try:
            user = Users.objects.get(cedula=cedula, estado='A')
            serializer = self.get_serializer(user)
            return Response({
                "codigo": status.HTTP_200_OK,
                "mensaje": "Usuario obtenido exitosamente",
                "detalle": serializer.data
            }, status=status.HTTP_200_OK)
        except Users.DoesNotExist:
            return Response({
                "codigo": status.HTTP_404_NOT_FOUND,
                "mensaje": "Usuario no encontrado",
                "detalle": None
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['put', 'patch'], url_path='actualizarPorCedula/(?P<cedula>[^/.]+)')
    def update_by_cedula(self, request, cedula=None):
        """
        [PUT/PATCH] /users/actualizarPorCedula/{cedula}/
        Actualiza los datos de un usuario buscándolo y validándolo a través de su cédula.
        """
        try:
            # 1. Validamos que exista un usuario activo con esa cédula
            user = Users.objects.get(cedula=cedula, estado='A')
        except Users.DoesNotExist:
            return Response({
                "codigo": status.HTTP_404_NOT_FOUND,
                "mensaje": "El usuario con la cédula proporcionada no existe o está inactivo.",
                "detalle": None
            }, status=status.HTTP_404_NOT_FOUND)

        # 2. 'PATCH' soporta actualizaciones parciales (solo los campos que envíes)
        partial = request.method == 'PATCH'
        
        # 3. Serializamos y validamos la data recibida
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                "codigo": status.HTTP_200_OK,
                "mensaje": "Usuario actualizado exitosamente",
                "detalle": serializer.data
            }, status=status.HTTP_200_OK)
            
        return Response({
            "codigo": status.HTTP_400_BAD_REQUEST,
            "mensaje": "Error de validación en los datos enviados",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'], url_path='eliminar/(?P<cedula>[^/.]+)')
    def delete_by_cedula(self, request, cedula=None):
        """
        [DELETE] /users/eliminar/{cedula}/
        Realiza un borrado lógico del usuario buscando por su cédula, cambiando su estado a inactivo ('N').
        """
        try:
            # Validamos que exista y esté activo
            user = Users.objects.get(cedula=cedula, estado='A')
        except Users.DoesNotExist:
            return Response({
                "codigo": status.HTTP_404_NOT_FOUND,
                "mensaje": "El usuario con la cédula proporcionada no existe o ya se encuentra inactivo.",
                "detalle": None
            }, status=status.HTTP_404_NOT_FOUND)

        # Borrado lógico: cambiamos el estado a 'N'
        user.estado = 'N'
        user.save()

        # Opcional: También dar de baja su asignación de rol en la empresa
        from apps.gestionEmpresas.models import EmpresaUsuarioRol
        EmpresaUsuarioRol.objects.filter(idUsuario=user).update(estado='N')

        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Usuario eliminado exitosamente.",
            "detalle": None
        }, status=status.HTTP_200_OK)