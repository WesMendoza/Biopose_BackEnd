from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from datetime import datetime

from .models import Empresa, Users, Rol, Menuoption
from .serializers import (
    EmpresaSerializer, 
    UsersSerializer, 
    RolSerializer, 
    MenuoptionSerializer,
    LoginSerializer
)
from .authentication import hash_password, generate_jwt, CustomJWTAuthentication

class AuthViewSet(viewsets.ViewSet):
    """
    Rutas de autenticación
    """
    permission_classes = [AllowAny]

    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            correo = serializer.validated_data['correo']
            password = serializer.validated_data['password']
            hashed_pass = hash_password(password)

            try:
                user = Users.objects.get(correo=correo, password=hashed_pass, estado='A')
                # Actualizar ultimoIngreso si se quiere
                user.ultimoIngreso = datetime.now()
                # user.save() # No podemos hacer save() directamente si mapped=False sin cuidado, pero intentemos 
                # Si managed=False no impide guardar si la tabla existe.

                token = generate_jwt(user)
                return Response({
                    "token": token,
                    "user": UsersSerializer(user).data
                }, status=status.HTTP_200_OK)
            except Users.DoesNotExist:
                return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

    def get_permissions(self):
        # Permitir registro sin token, requerir token para el resto (GET, PUT, DELETE)
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        # Encriptamos la contraseña si viene en la carga útil del request
        if 'password' in self.request.data:
            hashed_pass = hash_password(self.request.data['password'])
            serializer.save(password=hashed_pass)
        else:
            serializer.save()

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

