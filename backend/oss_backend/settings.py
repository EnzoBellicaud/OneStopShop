"""Django settings for the OneStopShop backend."""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def _parse_csv_env(var_name: str, default: str = "") -> list[str]:
    return [
        item.strip()
        for item in os.getenv(var_name, default).split(",")
        if item.strip()
    ]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = _parse_csv_env("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver")


# Application definition

INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'content',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'oss_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'oss_backend.wsgi.application'


POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "content")
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("POSTGRES_DB", "oss_db"),
        'USER': os.getenv("POSTGRES_USER", "oss_user"),
        'PASSWORD': os.getenv("POSTGRES_PASSWORD", "oss_password"),
        'HOST': os.getenv("POSTGRES_HOST", "localhost"),
        'PORT': os.getenv("POSTGRES_PORT", "5432"),
        'OPTIONS': {
            'options': f'-c search_path={POSTGRES_SCHEMA},public',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# API CORS configuration (Angular dev app calls the backend from another origin).
CORS_ALLOWED_ORIGINS = _parse_csv_env(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:4200,http://127.0.0.1:4200",
)
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"

# Scraper runtime configuration
SCRAPER_TIMEOUT_SECONDS = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "30"))
SCRAPER_INTERVAL_MINUTES = int(os.getenv("SCRAPER_INTERVAL_MINUTES", "360"))
SCRAPER_RUN_ON_START = os.getenv("SCRAPER_RUN_ON_START", "true").lower() == "true"
SCRAPER_LLM_FALLBACK_THRESHOLD = float(os.getenv("SCRAPER_LLM_FALLBACK_THRESHOLD", "0.60"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-coder:480b-cloud")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "45"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "content": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
