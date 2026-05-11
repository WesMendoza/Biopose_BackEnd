import jwt
import hashlib
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions
from .models import Users

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_jwt(user):
    payload = {
        'idUsuario': user.idUsuario,
        'correo': user.correo,
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
        except Users.DoesNotExist:
            raise exceptions.AuthenticationFailed('Usuario no encontrado')

        return (user, token)
