from rest_framework import serializers
from apps.users.models import Users

class LoginSerializer(serializers.Serializer):
    correo = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['nombre', 'apellido', 'cedula', 'correo', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class VerifyEmailSerializer(serializers.Serializer):
    correo = serializers.EmailField()

class VerifyCedulaSerializer(serializers.Serializer):
    cedula = serializers.CharField(max_length=20)
