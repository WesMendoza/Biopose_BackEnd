from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmpresaViewSet, RolViewSet,
    EmpresaUsuarioRolViewSet
)

router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet)
router.register(r'roles', RolViewSet, basename='rol')
router.register(r'asignarUsuarioRol', EmpresaUsuarioRolViewSet, basename='asignarUsuarioRol')

urlpatterns = [
    path('', include(router.urls)),
]
