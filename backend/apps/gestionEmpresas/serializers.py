from Biopose_BackEnd.backend.apps.menuOpciones.models import RolOption
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

class RolSerializer(serializers.ModelSerializer):
    # NUEVO: Le decimos que calcule este campo al vuelo
    menus_permitidos = serializers.SerializerMethodField()

    class Meta:
        model = Rol
        fields = '__all__'

    def get_menus_permitidos(self, obj):
        # Buscamos en la tabla intermedia todos los idOption que tiene este rol
        # Devuelve un array plano como: [1, 2, 5]
        return RolOption.objects.filter(idRol=obj).values_list('idOption_id', flat=True)
