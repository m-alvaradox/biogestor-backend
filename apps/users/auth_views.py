"""Authentication endpoints: /api/v1/auth/csrf|login|refresh|logout|me/."""

from django.conf import settings
from django.contrib.auth.models import update_last_login
from django.core.exceptions import ObjectDoesNotExist
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .authentication import (
    delete_refresh_cookie,
    enforce_csrf,
    get_profile,
    set_refresh_cookie,
    user_can_authenticate,
)
from .models import User
from .serializers import CurrentUserSerializer, LoginSerializer

INVALID_CREDENTIALS = "Correo o contraseña incorrectos."
INVALID_SESSION = "La sesión no es válida o expiró. Inicia sesión de nuevo."


class PublicAuthView(APIView):
    """Base for the auth endpoints that are called before having an access token."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get_authenticate_header(self, request):
        # Without authentication classes DRF would turn 401 into 403.
        return 'Bearer realm="api"'


class CsrfView(PublicAuthView):
    """Sets the CSRF cookie the frontend must echo back in a header."""

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"csrf_token": get_token(request)})


class LoginView(PublicAuthView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        profile = User.objects.select_related("account").filter(email__iexact=email).first()
        account = profile.account if profile else None
        # Same message for unknown email, wrong password or inactive user,
        # so the response does not reveal which accounts exist.
        if (
            account is None
            or not account.check_password(password)
            or not user_can_authenticate(account)
        ):
            raise AuthenticationFailed(INVALID_CREDENTIALS, code="invalid_credentials")

        refresh = RefreshToken.for_user(account)
        update_last_login(None, account)

        response = Response(
            {
                "access": str(refresh.access_token),
                "user": CurrentUserSerializer(profile).data,
            }
        )
        set_refresh_cookie(response, str(refresh))
        return response


class RefreshView(PublicAuthView):
    """Issues a new access token from the refresh cookie and rotates the cookie."""

    def post(self, request):
        enforce_csrf(request)
        refresh = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME)
        if not refresh:
            raise AuthenticationFailed(INVALID_SESSION, code="refresh_missing")

        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, ObjectDoesNotExist):
            # Expired, malformed or blacklisted token, or the account was deleted.
            response = Response({"detail": INVALID_SESSION}, status=status.HTTP_401_UNAUTHORIZED)
            delete_refresh_cookie(response)
            return response

        response = Response({"access": serializer.validated_data["access"]})
        set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


class LogoutView(PublicAuthView):
    """Blacklists the refresh token and removes its cookie.

    The access token is not revoked; it expires on its own (short lifetime).
    """

    def post(self, request):
        enforce_csrf(request)
        refresh = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME)
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass  # Already invalid: nothing to revoke.

        response = Response(status=status.HTTP_204_NO_CONTENT)
        delete_refresh_cookie(response)
        return response


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CurrentUserSerializer(get_profile(request.user)).data)
