"""Configuración base de Django para BioGestor."""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DJANGO_DEBUG", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY es obligatorio cuando DJANGO_DEBUG está desactivado."
        )
    SECRET_KEY = "django-insecure-local-development-only-not-for-production"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "apps.core.apps.CoreConfig",
    "apps.users.apps.UsersConfig",
    "apps.datasets.apps.DatasetsConfig",
    "apps.ml_models.apps.MlModelsConfig",
    "apps.experiments.apps.ExperimentsConfig",
    "apps.observations.apps.ObservationsConfig",
    "apps.integrations.apps.IntegrationsConfig",
    "apps.audit.apps.AuditConfig",
    "apps.storage.apps.StorageConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "biogestor"),
        "USER": os.getenv("POSTGRES_USER", "biogestor"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Las vistas DRF requieren autenticación de manera predeterminada.
# Los endpoints públicos deberán declararse explícitamente.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.users.authentication.PlatformJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Autenticación JWT (S2-06 / S2-07).
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=24),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "USER_AUTHENTICATION_RULE": "apps.users.authentication.user_can_authenticate",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# El refresh token viaja solo en una cookie HttpOnly limitada a /api/v1/auth/.
AUTH_REFRESH_COOKIE_NAME = "biogestor_refresh"
AUTH_REFRESH_COOKIE_PATH = "/api/v1/auth/"
AUTH_REFRESH_COOKIE_SAMESITE = "Lax"
AUTH_REFRESH_COOKIE_SECURE = os.getenv("DJANGO_AUTH_COOKIE_SECURE", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Nombres que Angular (HttpClient) usa por defecto para la protección CSRF.
CSRF_COOKIE_NAME = "XSRF-TOKEN"
CSRF_HEADER_NAME = "HTTP_X_XSRF_TOKEN"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = AUTH_REFRESH_COOKIE_SECURE
