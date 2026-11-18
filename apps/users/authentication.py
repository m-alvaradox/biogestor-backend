"""JWT authentication for BioGestor (S2-07, mechanism defined in S2-06).

- Access token: short-lived, returned in the JSON body (kept in memory by the frontend).
- Refresh token: stored in an HttpOnly cookie restricted to the auth endpoints,
  rotated on every use and blacklisted afterwards.
"""

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication


def get_profile(account):
    """Return the platform user linked to a Django account, or None."""
    if account is None:
        return None
    try:
        return account.profile
    except ObjectDoesNotExist:
        return None


def user_can_authenticate(account):
    """Both the Django account and the platform user must be active.

    Used as SIMPLE_JWT["USER_AUTHENTICATION_RULE"], so it also applies on refresh.
    """
    profile = get_profile(account)
    return bool(account is not None and account.is_active and profile and profile.is_active)


class PlatformJWTAuthentication(JWTAuthentication):
    """JWT authentication that also rejects users deactivated in the platform."""

    def get_user(self, validated_token):
        account = super().get_user(validated_token)
        if not user_can_authenticate(account):
            raise AuthenticationFailed("El usuario está inactivo.", code="user_inactive")
        return account


def enforce_csrf(request):
    """Run Django's CSRF check on a DRF request (DRF views are CSRF-exempt by default).

    Needed for the endpoints that rely on the refresh cookie.
    """
    check = CSRFCheck(lambda _request: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise PermissionDenied("Falta el token CSRF o no es válido.")


def set_refresh_cookie(response, refresh_token):
    response.set_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        secure=settings.AUTH_REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
    )


def delete_refresh_cookie(response):
    response.delete_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
    )
