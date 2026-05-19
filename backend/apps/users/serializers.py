from rest_framework import serializers
from .models import Empresa, Users, Rol, Menuoption

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}
        }

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class MenuoptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menuoption
        fields = '__all__'

