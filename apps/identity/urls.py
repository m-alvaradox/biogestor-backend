from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("usuarios", views.UsuarioViewSet, basename="usuario")

urlpatterns = [
    path("auth/login/", views.login, name="auth-login"),
    path("auth/logout/", views.logout, name="auth-logout"),
    path("auth/perfil/", views.perfil, name="auth-perfil"),
    *router.urls,
]
