from rest_framework import serializers

from .models import Usuario
from .permisos import operaciones_de


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class PerfilSerializer(serializers.ModelSerializer):
    """Lo que el frontend necesita saber del usuario que inició sesión."""

    rol_nombre = serializers.CharField(source="get_rol_display", read_only=True)
    operaciones = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "rol",
            "rol_nombre",
            "departamento",
            "operaciones",
        ]
        read_only_fields = fields

    def get_operaciones(self, usuario):
        return operaciones_de(usuario)


class UsuarioSerializer(serializers.ModelSerializer):
    """Gestión de usuarios (solo Administrador)."""

    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "rol",
            "departamento",
            "is_active",
            "password",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Es obligatoria al crear un usuario."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        usuario = Usuario(**validated_data)
        usuario.set_password(password)  # nunca guardar la contraseña en texto plano
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
