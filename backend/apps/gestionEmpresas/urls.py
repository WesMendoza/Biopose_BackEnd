from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmpresaViewSet, RolViewSet, MenuoptionViewSet, 
    EmpresaUsuarioRolViewSet, RolOptionViewSet
)

router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet)
router.register(r'roles', RolViewSet)
router.register(r'menu-opciones', MenuoptionViewSet)
router.register(r'asignar-usuario-rol', EmpresaUsuarioRolViewSet, basename='asignar-user-rol')
router.register(r'asignar-rol-opcion', RolOptionViewSet, basename='asignar-rol-opcion')

urlpatterns = [
    path('', include(router.urls)),
]
