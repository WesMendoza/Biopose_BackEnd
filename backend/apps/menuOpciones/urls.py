from django.urls import path, include
from rest_framework.routers import DefaultRouter

# IMPORTANTE: Asegúrate de importar ConfiguracionRutasView aquí
from .views import MenuOpcionViewSet, RolOptionViewSet, ConfiguracionRutasView

router = DefaultRouter()
router.register(r'opciones', MenuOpcionViewSet, basename='menuOpcion')
router.register(r'asignarRolOpcion', RolOptionViewSet, basename='asignarRolOpcion')

urlpatterns = [
    # 1. Agregamos nuestra nueva ruta MANUALMENTE
    path('rutas/configurar/', ConfiguracionRutasView.as_view(), name='configurar_rutas'),
    
    # 2. Dejamos el router que ya tenías para el resto de cosas
    path('', include(router.urls)),
]