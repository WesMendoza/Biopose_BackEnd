from rest_framework import viewsets
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

class UsersViewSet(viewsets.ModelViewSet):
    """
    Controlador (ViewSet) para operaciones CRUD sobre Users
    """
    queryset = Users.objects.all()
    serializer_class = UsersSerializer

class RolViewSet(viewsets.ModelViewSet):
    """
    Controlador (ViewSet) para operaciones CRUD sobre Rol
    """
    queryset = Rol.objects.all()
    serializer_class = RolSerializer

class MenuoptionViewSet(viewsets.ModelViewSet):
    """
    Controlador (ViewSet) para operaciones CRUD sobre Menuoption
    """
    queryset = Menuoption.objects.all()
    serializer_class = MenuoptionSerializer

