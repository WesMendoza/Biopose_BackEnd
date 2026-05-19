from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmpresaViewSet, UsersViewSet, RolViewSet, MenuoptionViewSet

router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet)
router.register(r'', UsersViewSet)  # Registramos Users directamente en la raíz de api/users/
router.register(r'roles', RolViewSet)
router.register(r'menu-opciones', MenuoptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
