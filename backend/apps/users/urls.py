from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsersViewSet

router = DefaultRouter()
router.register(r'', UsersViewSet)  # Registramos Users directamente en la raíz de api/users/

urlpatterns = [
    path('', include(router.urls)),
]
