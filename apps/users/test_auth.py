"""Authentication tests (S2-07): valid and invalid login, refresh, logout and protection."""

from datetime import timedelta
from io import StringIO
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import User

PASSWORD = "Tilapia-segura-2026"
COOKIE = settings.AUTH_REFRESH_COOKIE_NAME


def create_user_with_password(email="ana@example.com", password=PASSWORD, **fields):
    account = get_user_model().objects.create_user(username=email, password=password)
    return User.objects.create(name="Ana Lima", email=email, account=account, **fields)


class LoginTests(APITestCase):
    url = reverse("auth-login")

    def setUp(self):
        self.profile = create_user_with_password()

    def login(self, email="ana@example.com", password=PASSWORD):
        return self.client.post(self.url, {"email": email, "password": password}, format="json")

    def test_valid_credentials_return_access_token_and_refresh_cookie(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body), {"access", "user"})
        self.assertEqual(body["user"]["email"], "ana@example.com")
        self.assertNotIn("refresh", body)
        cookie = response.cookies[COOKIE]
        self.assertTrue(cookie.value)
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["path"], "/api/v1/auth/")
        self.assertEqual(cookie["samesite"], "Lax")

    def test_access_token_lasts_15_minutes(self):
        token = AccessToken(self.login().json()["access"])

        self.assertEqual(token.lifetime, timedelta(minutes=15))

    def test_email_is_case_insensitive(self):
        self.assertEqual(self.login(email="ANA@example.com").status_code, 200)

    def test_invalid_credentials_return_401_with_the_same_message(self):
        cases = {
            "wrong password": {"password": "otra-clave"},
            "unknown email": {"email": "nadie@example.com"},
        }
        for case, data in cases.items():
            with self.subTest(case):
                response = self.login(**data)

                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()["detail"], "Correo o contraseña incorrectos.")
                self.assertNotIn(COOKIE, response.cookies)

    def test_inactive_user_cannot_log_in(self):
        self.profile.status = User.UserStatus.INACTIVE
        self.profile.save()

        self.assertEqual(self.login().status_code, 401)

    def test_user_without_account_cannot_log_in(self):
        User.objects.create(name="Sin cuenta", email="sincuenta@example.com")

        self.assertEqual(self.login(email="sincuenta@example.com").status_code, 401)

    def test_missing_fields_return_400(self):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()), {"email", "password"})


class ProtectedEndpointTests(APITestCase):
    def setUp(self):
        create_user_with_password()
        response = self.client.post(
            reverse("auth-login"),
            {"email": "ana@example.com", "password": PASSWORD},
            format="json",
        )
        self.access = response.json()["access"]

    def test_protected_endpoints_return_401_without_token(self):
        for name in ["dataset-list", "user-list", "auth-me"]:
            with self.subTest(name):
                response = self.client.get(reverse(name))

                self.assertEqual(response.status_code, 401)
                self.assertIn("Bearer", response["WWW-Authenticate"])

    def test_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer not-a-token")

        self.assertEqual(self.client.get(reverse("dataset-list")).status_code, 401)

    def test_valid_token_gives_access(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

        self.assertEqual(self.client.get(reverse("dataset-list")).status_code, 200)
        me = self.client.get(reverse("auth-me"))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], "ana@example.com")

    def test_token_stops_working_when_user_is_deactivated(self):
        User.objects.filter(email="ana@example.com").update(status=User.UserStatus.INACTIVE)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 401)

    def test_health_stays_public(self):
        self.assertEqual(self.client.get(reverse("health")).status_code, 200)


class RefreshAndLogoutTests(APITestCase):
    def setUp(self):
        self.profile = create_user_with_password()
        self.client.post(
            reverse("auth-login"),
            {"email": "ana@example.com", "password": PASSWORD},
            format="json",
        )

    def test_refresh_returns_new_access_and_rotates_cookie(self):
        old_refresh = self.client.cookies[COOKIE].value

        response = self.client.post(reverse("auth-refresh"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertNotEqual(response.cookies[COOKIE].value, old_refresh)

    def test_old_refresh_token_cannot_be_reused_after_rotation(self):
        old_refresh = self.client.cookies[COOKIE].value
        self.client.post(reverse("auth-refresh"))
        self.client.cookies[COOKIE] = old_refresh

        self.assertEqual(self.client.post(reverse("auth-refresh")).status_code, 401)

    def test_refresh_without_cookie_returns_401(self):
        del self.client.cookies[COOKIE]

        self.assertEqual(self.client.post(reverse("auth-refresh")).status_code, 401)

    def test_refresh_fails_for_inactive_user(self):
        self.profile.status = User.UserStatus.INACTIVE
        self.profile.save()

        self.assertEqual(self.client.post(reverse("auth-refresh")).status_code, 401)

    def test_logout_deletes_cookie_and_revokes_refresh_token(self):
        refresh = self.client.cookies[COOKIE].value

        response = self.client.post(reverse("auth-logout"))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.cookies[COOKIE].value, "")
        self.client.cookies[COOKIE] = refresh
        self.assertEqual(self.client.post(reverse("auth-refresh")).status_code, 401)

    def test_logout_without_cookie_is_harmless(self):
        del self.client.cookies[COOKIE]

        self.assertEqual(self.client.post(reverse("auth-logout")).status_code, 204)


class CsrfTests(APITestCase):
    def setUp(self):
        create_user_with_password()
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.post(
            reverse("auth-login"),
            {"email": "ana@example.com", "password": PASSWORD},
            format="json",
        )

    def test_refresh_and_logout_require_csrf_token(self):
        for name in ["auth-refresh", "auth-logout"]:
            with self.subTest(name):
                self.assertEqual(self.client.post(reverse(name)).status_code, 403)

    def test_refresh_works_with_csrf_token_from_csrf_endpoint(self):
        csrf = self.client.get(reverse("auth-csrf")).json()["csrf_token"]

        response = self.client.post(reverse("auth-refresh"), HTTP_X_XSRF_TOKEN=csrf)

        self.assertEqual(response.status_code, 200)


class SetUserPasswordCommandTests(TestCase):
    def run_command(self, email, *passwords):
        with mock.patch("getpass.getpass", side_effect=passwords):
            call_command("set_user_password", email, stdout=StringIO())

    def test_creates_account_and_allows_login(self):
        profile = User.objects.create(name="Ana Lima", email="ana@example.com")

        self.run_command("ana@example.com", PASSWORD, PASSWORD)

        profile.refresh_from_db()
        self.assertTrue(profile.account.check_password(PASSWORD))

    def test_changes_existing_password(self):
        profile = create_user_with_password()

        self.run_command("ana@example.com", "Nueva-clave-2026", "Nueva-clave-2026")

        profile.account.refresh_from_db()
        self.assertTrue(profile.account.check_password("Nueva-clave-2026"))

    def test_rejects_unknown_email_mismatch_and_weak_password(self):
        User.objects.create(name="Ana Lima", email="ana@example.com")
        cases = {
            "unknown email": ("nadie@example.com", PASSWORD, PASSWORD),
            "mismatch": ("ana@example.com", PASSWORD, "otra"),
            "weak": ("ana@example.com", "123", "123"),
        }
        for case, args in cases.items():
            with self.subTest(case), self.assertRaises(CommandError):
                self.run_command(*args)
