from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MenuOpcionViewSet, RolOptionViewSet

router = DefaultRouter()
router.register(r'opciones', MenuOpcionViewSet, basename='menuOpcion')
router.register(r'asignarRolOpcion', RolOptionViewSet, basename='asignarRolOpcion')

urlpatterns = [
    path('', include(router.urls)),
]
