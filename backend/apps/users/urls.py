from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmpresaViewSet, UsersViewSet, RolViewSet, MenuoptionViewSet, AuthViewSet

router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet)
router.register(r'usuarios', UsersViewSet)
router.register(r'roles', RolViewSet)
router.register(r'menu-opciones', MenuoptionViewSet)

urlpatterns = [
    path('login/', AuthViewSet.as_view({'post': 'login'}), name='login'),
    path('', include(router.urls)),
]
