import jwt
import hashlib
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions
from apps.users.models import Users

# IMPORTANTE: Importar el modelo de la relación empresa-usuario
from apps.gestionEmpresas.models import EmpresaUsuarioRol

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_jwt(user):
    # Forzamos la búsqueda usando el idUsuario directamente
    # y asegurándonos de traer el idEmpresa asociado a la empresa activa
    empresa_usuario = EmpresaUsuarioRol.objects.filter(
        idUsuario__idUsuario=user.idUsuario, 
        estado='A'
    ).select_related('idRol').first() # select_related optimiza la consulta cruzada con la tabla Rol
    
    id_empresa = None
    id_rol = None
    nombre_rol = None

    if empresa_usuario:
        id_empresa = empresa_usuario.idEmpresa_id
        id_rol = empresa_usuario.idRol_id
        if empresa_usuario.idRol:
            nombre_rol = empresa_usuario.idRol.nombreRol

    payload = {
        'idUsuario': user.idUsuario,
        'correo': user.correo,
        'idEmpresa': id_empresa, 
        'idRol': id_rol,             
        'nombreRol': nombre_rol,     
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    
    secret = getattr(settings, 'SECRET_KEY', 'default-secret-key')
    return jwt.encode(payload, secret, algorithm='HS256')

class CustomJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split()
            if prefix.lower() != 'bearer':
                return None
        except ValueError:
            return None

        secret = getattr(settings, 'SECRET_KEY', 'default-secret-key')
        try:
            payload = jwt.decode(token, secret, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('El token ha expirado')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Token inválido')

        try:
            user = Users.objects.get(idUsuario=payload.get('idUsuario'))
            
            # BONUS: Pegamos los datos extraídos del token al objeto user.
            # Así, en cualquier View de Django puedes usar: request.user.idEmpresa_jwt
            user.idEmpresa_jwt = payload.get('idEmpresa')
            user.idRol_jwt = payload.get('idRol')              # <--- Disponible en Django
            user.nombreRol_jwt = payload.get('nombreRol')      # <--- Disponible en Django
            
        except Users.DoesNotExist:
            raise exceptions.AuthenticationFailed('Usuario no encontrado')

        return (user, token)