from rest_framework import serializers
from .models import Empresa, Rol, EmpresaUsuarioRol

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class EmpresaUsuarioRolSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaUsuarioRol
        fields = '__all__'


