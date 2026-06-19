from apps.menuOpciones.models import RolOption
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
    # === NUEVO: Declaramos un campo calculado ===
    menus_permitidos = serializers.SerializerMethodField()

    class Meta:
        model = Rol
        fields = '__all__' # Si aquí tienes una lista explícita en lugar de '__all__', asegúrate de agregar 'menus_permitidos' a la lista.

    # === NUEVO: Función que calcula qué permisos tiene este rol ===
    def get_menus_permitidos(self, obj):
        # Busca en la tabla RolOption todas las opciones activas para este rol
        # y devuelve una lista plana solo con los IDs de las pantallas. Ej: [1, 2, 5]
        return list(RolOption.objects.filter(idRol=obj, estado='A').values_list('idOption', flat=True))
