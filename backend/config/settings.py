"""
Production-grade Django settings for AI Career Intelligence Platform.
"""
from pathlib import Path
from datetime import timedelta

import environ

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, ''),
    ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    DATABASE_URL=(str, 'postgresql://localhost/skill_gap_analyzer_db'),
    JWT_ACCESS_EXPIRY=(int, 900),
    JWT_REFRESH_EXPIRY=(int, 604800),
    GROQ_API_KEY=(str, ''),
    ADZUNA_APP_ID=(str, ''),
    ADZUNA_API_KEY=(str, ''),
)

BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(BASE_DIR.parent / '.env')

SECRET_KEY = env('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('SECRET_KEY environment variable is required')

DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
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
    'core.middleware.CSRFCookieMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RateLimitMiddleware',
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

DATABASES = {'default': env.db()}

AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = ['apps.accounts.backends.EmailBackend']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.accounts.authentication.JWTCookieAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

JWT_CONFIG = {
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=env('JWT_ACCESS_EXPIRY')),
    'REFRESH_TOKEN_LIFETIME': timedelta(seconds=env('JWT_REFRESH_EXPIRY')),
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

COOKIE_CONFIG = {
    'ACCESS_COOKIE_NAME': 'access_token',
    'REFRESH_COOKIE_NAME': 'refresh_token',
    'HTTPONLY': True,
    'SECURE': not DEBUG,
    'SAMESITE': 'Lax',
    'MAX_AGE_ACCESS': env('JWT_ACCESS_EXPIRY'),
    'MAX_AGE_REFRESH': env('JWT_REFRESH_EXPIRY'),
}


EMBEDDING_CONFIG = {
    'MODEL_NAME': 'all-MiniLM-L6-v2',
    'DIMENSION': 384,

}
TESTING = False 

ADZUNA_CONFIG = {
    'APP_ID': env('ADZUNA_APP_ID'),
    'API_KEY': env('ADZUNA_API_KEY'),
    'BASE_URL': 'https://api.adzuna.com/v1/api/jobs',
}

GROQ_API_KEY = env("GROQ_API_KEY")

GROQ_CONFIG = {
    "API_KEY": GROQ_API_KEY,
}