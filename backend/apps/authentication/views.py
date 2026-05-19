from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from datetime import datetime

from apps.users.models import Users
from apps.users.serializers import UsersSerializer
from .serializers import LoginSerializer, RegisterSerializer, VerifyEmailSerializer, VerifyCedulaSerializer
from .utils import hash_password, generate_jwt

class AuthViewSet(viewsets.ViewSet):
    """
    Rutas de autenticación
    """
    permission_classes = [AllowAny]
    #Metodo Login, recibe correo y contraseña, valida y retorna token JWT
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            correo = serializer.validated_data['correo']
            password = serializer.validated_data['password']
            hashed_pass = hash_password(password)

            try:
                user = Users.objects.get(correo=correo, password=hashed_pass, estado='A')
                user.ultimoIngreso = datetime.now()

                token = generate_jwt(user)
                return Response({
                    "codigo": 200,
                    "mensaje": "Inicio de sesión exitoso",
                    "detalle": {
                        "token": token,
                        # "user": UsersSerializer(user).data
                    }
                }, status=status.HTTP_200_OK)
            except Users.DoesNotExist:
                return Response({
                    "codigo": 401,
                    "mensaje": "No autorizado",
                    "detalle": "Credenciales inválidas o usuario inactivo"
                }, status=status.HTTP_401_UNAUTHORIZED)
            
        return Response({
            "codigo": 400,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    #Metodo Register, recibe datos del usuario, valida y crea una nueva cuenta
    @action(detail=False, methods=['post'])
    def registerAccount(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            params = serializer.validated_data
            if Users.objects.filter(correo=params['correo']).exists():
                return Response({
                    "codigo": 400,
                    "mensaje": "Error en registro",
                    "detalle": "El correo ya está en uso."
                }, status=status.HTTP_400_BAD_REQUEST)
            if 'cedula' in params and Users.objects.filter(cedula=params['cedula']).exists():
                return Response({
                    "codigo": 400,
                    "mensaje": "Error en registro",
                    "detalle": "La cédula ya está registrada."
                }, status=status.HTTP_400_BAD_REQUEST)

            hashed_pass = hash_password(params['password'])
            user = serializer.save(password=hashed_pass, estado='A')
            return Response({
                "codigo": 201,
                "mensaje": "Cuenta creada exitosamente",
                "detalle": UsersSerializer(user).data
            }, status=status.HTTP_201_CREATED)
            
        return Response({
            "codigo": 400,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    #Metodo para verificar si una cédula ya existe en la base de datos
    @action(detail=False, methods=['post'], url_path='verifyCedula')
    def verifyCedula(self, request):
        serializer = VerifyCedulaSerializer(data=request.data)
        if serializer.is_valid():
            exists = Users.objects.filter(cedula=serializer.validated_data['cedula']).exists()
            return Response({
                "codigo": 200,
                "mensaje": "Verificación completada",
                "detalle": {"exists": exists}
            }, status=status.HTTP_200_OK)
            
        return Response({
            "codigo": 400,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    #Metodo para verificar si un correo ya existe en la base de datos
    @action(detail=False, methods=['post'], url_path='verifyEmail')
    def verifyEmail(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            exists = Users.objects.filter(correo=serializer.validated_data['correo']).exists()
            return Response({
                "codigo": 200,
                "mensaje": "Verificación completada",
                "detalle": {"exists": exists}
            }, status=status.HTTP_200_OK)
            
        return Response({
            "codigo": 400,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)