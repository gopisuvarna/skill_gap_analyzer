"""Test settings — uses SQLite, all secrets from environment variables."""
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-test-key-for-testing-only")
DEBUG = True
ALLOWED_HOSTS = ['*']
TESTING = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'apps.accounts',
    'apps.documents.apps.DocumentsConfig',
    'apps.skills',
    'apps.roles',
    'apps.embeddings',
    'apps.recommendations',
    'apps.jobs.apps.JobsConfig',
    'apps.analytics',
    'apps.chatbot',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = ['apps.accounts.backends.EmailBackend']

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
APPEND_SLASH = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.accounts.authentication.JWTCookieAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

JWT_CONFIG = {
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=900),
    'REFRESH_TOKEN_LIFETIME': timedelta(seconds=604800),
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

COOKIE_CONFIG = {
    'ACCESS_COOKIE_NAME': 'access_token',
    'REFRESH_COOKIE_NAME': 'refresh_token',
    'HTTPONLY': True,
    'SECURE': False,
    'SAMESITE': 'Lax',
    'MAX_AGE_ACCESS': 900,
    'MAX_AGE_REFRESH': 604800,
}

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

EMBEDDING_CONFIG = {
    'MODEL_NAME': 'all-MiniLM-L6-v2',
    'DIMENSION': 384,
}

ADZUNA_CONFIG = {
    'APP_ID':   os.environ.get("ADZUNA_APP_ID", ""),
    'API_KEY':  os.environ.get("ADZUNA_API_KEY", ""),
    'BASE_URL': 'https://api.adzuna.com/v1/api/jobs',
}

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_CONFIG = {
    "API_KEY": GROQ_API_KEY,
}