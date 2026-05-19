from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .models import Empresa, Users, Rol, Menuoption
from .serializers import (
    EmpresaSerializer, 
    UsersSerializer, 
    RolSerializer, 
    MenuoptionSerializer
)

class EmpresaViewSet(viewsets.ModelViewSet):
    """
    Controlador (ViewSet) para operaciones CRUD sobre Empresa
    """
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAuthenticated]

class UsersViewSet(viewsets.ModelViewSet):
    """
    Controlador (ViewSet) para operaciones CRUD sobre Users
    """
    queryset = Users.objects.filter(estado='A')  # Solo listar usuarios activos por defecto
    serializer_class = UsersSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        """
        Sobrescribimos el destroy para hacer un borrado lógico
        """
        user = self.get_object()
        user.estado = 'I'
        # user.save() # Ajustar según si allows save() directo en DB manual
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='cedula/(?P<cedula>[^/.]+)')
    def get_by_cedula(self, request, cedula=None):
        """
        Obtener usuario por cédula
        """
        try:
            user = Users.objects.get(cedula=cedula, estado='A')
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Users.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

class RolViewSet(viewsets.ModelViewSet):
    """
    Controlador (ViewSet) para operaciones CRUD sobre Rol
    """
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

class MenuoptionViewSet(viewsets.ModelViewSet):
    """
    Controlador (ViewSet) para operaciones CRUD sobre Menuoption
    """
    queryset = Menuoption.objects.all()
    serializer_class = MenuoptionSerializer
    permission_classes = [IsAuthenticated]