"""Login, perfil y gestión de usuarios."""

from django.contrib.auth import authenticate
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Usuario
from .permisos import Operacion, requiere
from .serializers import LoginSerializer, PerfilSerializer, UsuarioSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Recibe usuario y contraseña; devuelve un token y el perfil."""
    datos = LoginSerializer(data=request.data)
    datos.is_valid(raise_exception=True)
    usuario = authenticate(
        request,
        username=datos.validated_data["username"],
        password=datos.validated_data["password"],
    )
    # authenticate() devuelve None si la contraseña es incorrecta o la cuenta está inactiva.
    if usuario is None:
        return Response(
            {"detail": "Usuario o contraseña incorrectos."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    token, _ = Token.objects.get_or_create(user=usuario)
    return Response({"token": token.key, "usuario": PerfilSerializer(usuario).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """Borra el token: el siguiente request con ese token dará 401."""
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def perfil(request):
    return Response(PerfilSerializer(request.user).data)


class UsuarioViewSet(viewsets.ModelViewSet):
    """CRUD de usuarios. Solo el Administrador."""

    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [requiere(Operacion.GESTIONAR_USUARIOS)]

    def get_queryset(self):
        qs = super().get_queryset()
        rol = self.request.query_params.get("rol")
        departamento = self.request.query_params.get("departamento")
        if rol:
            qs = qs.filter(rol=rol)
        if departamento:
            qs = qs.filter(departamento__iexact=departamento)
        return qs

    def perform_destroy(self, instance):
        # No se borra: el usuario puede ser propietario de datasets (PROTECT) y
        # aparecer en la auditoría. Se desactiva y se le quita el token.
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        Token.objects.filter(user=instance).delete()
