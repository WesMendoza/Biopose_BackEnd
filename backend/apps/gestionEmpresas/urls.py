from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmpresaViewSet, RolViewSet, MenuoptionViewSet, 
    EmpresaUsuarioRolViewSet, RolOptionViewSet
)

router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet)
router.register(r'roles', RolViewSet, basename='rol')
router.register(r'menuOpciones', MenuoptionViewSet)
router.register(r'asignarUsuarioRol', EmpresaUsuarioRolViewSet, basename='asignarUsuarioRol')
router.register(r'asignarRolOpcion', RolOptionViewSet, basename='asignarRolOpcion')

urlpatterns = [
    path('', include(router.urls)),
]
