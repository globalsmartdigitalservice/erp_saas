import datetime
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "Falta DJANGO_SECRET_KEY. Copie .env.example a .env y complétela."
    )


APPS_DJANGO = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

APPS_TERCEROS = [
    "strawberry_django",
]

APPS_PROPIAS = [
    "comun.usuarios",
    "comun.membresias",
    "comun.tipologias",
    "comun.geografia",
    "comun.monedas",
    "comun.idiomas",
    "comun.empresas",
    "comun.tipos_documento",
    "comun.catalogo_modulos",
    "servicios.numeracion",
    "servicios.integraciones",
    "dominios.entidades",
    "dominios.seguridad",
]

INSTALLED_APPS = APPS_DJANGO + APPS_TERCEROS + APPS_PROPIAS


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "core.tenancy.middleware.EmpresaDesdeCabeceraMiddleware",
    "dominios.seguridad.middleware.SesionPorTokenMiddleware",
    "core.idioma.middleware.IdiomaDesdeCabeceraMiddleware",
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

ASGI_APPLICATION = "config.asgi.application"
WSGI_APPLICATION = "config.wsgi.application"


GRAPHQL_HABILITADO = False

TENANCY_POR_CABECERA = False


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "erp"),
        "USER": os.getenv("DB_USER", "erp"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTH_USER_MODEL = "usuarios.Usuario"

AUTHENTICATION_BACKENDS = ["dominios.seguridad.autenticacion.BackendDeEmpresa"]


JWT_VIDA_ACCESO = datetime.timedelta(minutes=15)
JWT_VIDA_REFRESH = datetime.timedelta(days=7)

COOKIE_ACCESO = "erp_acceso"
COOKIE_REFRESH = "erp_refresh"

COOKIE_HTTPONLY = True

COOKIE_SAMESITE = "Lax"

USE_HTTPS = os.getenv("USE_HTTPS", "false").lower() == "true"
COOKIE_SECURE = USE_HTTPS


PROXIES_CONFIABLES = int(os.getenv("PROXIES_CONFIABLES", "0"))

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {
            "user_attributes": (
                "username",
                "first_name",
                "last_name",
                "seg_apellido",
                "email",
            )
        },
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "es-bo"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "erp": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "consola": {
            "class": "logging.StreamHandler",
            "formatter": "erp",
        },
    },
    "loggers": {
        "erp": {
            "handlers": ["consola"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
