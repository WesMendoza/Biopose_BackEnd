from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Empresa, Rol, Menuoption, EmpresaUsuarioRol, RolOption
from .serializers import (
    EmpresaSerializer, RolSerializer, MenuoptionSerializer, 
    EmpresaUsuarioRolSerializer, RolOptionSerializer
)

class BaseStandardViewSet(viewsets.ModelViewSet):
    """
    ViewSet base para unificar las respuestas con el formato:
    { codigo, mensaje, detalle }
    """
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": f"Lista obtenida exitosamente",
            "detalle": serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": f"Registro obtenido exitosamente",
            "detalle": serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "codigo": status.HTTP_201_CREATED,
                "mensaje": "Registro creado exitosamente",
                "detalle": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "codigo": status.HTTP_400_BAD_REQUEST,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                "codigo": status.HTTP_200_OK,
                "mensaje": "Registro actualizado exitosamente",
                "detalle": serializer.data
            })
        return Response({
            "codigo": status.HTTP_400_BAD_REQUEST,
            "mensaje": "Error de validación",
            "detalle": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "codigo": status.HTTP_200_OK,
            "mensaje": "Registro eliminado exitosamente",
            "detalle": None
        }, status=status.HTTP_200_OK)


class EmpresaViewSet(BaseStandardViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAuthenticated]


class RolViewSet(BaseStandardViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]


class MenuoptionViewSet(BaseStandardViewSet):
    queryset = Menuoption.objects.all()
    serializer_class = MenuoptionSerializer
    permission_classes = [IsAuthenticated]

class EmpresaUsuarioRolViewSet(BaseStandardViewSet):
    """ ViewSet para 'asignar' y gestionar la relación Empresa-Usuario-Rol """
    queryset = EmpresaUsuarioRol.objects.all()
    serializer_class = EmpresaUsuarioRolSerializer
    permission_classes = [IsAuthenticated]

class RolOptionViewSet(BaseStandardViewSet):
    """ ViewSet para 'asignar' y gestionar opciones de menú a los Roles """
    queryset = RolOption.objects.all()
    serializer_class = RolOptionSerializer
    permission_classes = [IsAuthenticated]
