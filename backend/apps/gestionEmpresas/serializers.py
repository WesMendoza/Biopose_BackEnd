from rest_framework import serializers
from .models import Empresa, Rol, Menuoption, EmpresaUsuarioRol, RolOption

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class MenuoptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menuoption
        fields = '__all__'

class EmpresaUsuarioRolSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaUsuarioRol
        fields = '__all__'

class RolOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolOption
        fields = '__all__'


