from rest_framework import serializers
from .models import MenuOpcion, RolOption

class MenuOpcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuOpcion
        fields = '__all__'

class RolOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolOption
        fields = '__all__'
