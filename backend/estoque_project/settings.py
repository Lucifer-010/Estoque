import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-estoque-prod-test-key-592837418293')

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

# Allowed Hosts configuration for api.estoquee.xyz and deployment environments
ALLOWED_HOSTS_ENV = os.getenv('DJANGO_ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = [
        'api.estoquee.xyz',
        'estoquee.xyz',
        'www.estoquee.xyz',
        '.estoquee.xyz',
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        'web',
        '*',
    ]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    # Estoque Domain Apps
    'apps.accounts',
    'apps.inventory',
    'apps.orders',
    'apps.blockchain',
    'apps.analytics',
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

ROOT_URLCONF = 'estoque_project.urls'

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

WSGI_APPLICATION = 'estoque_project.wsgi.application'

# Database configuration: PostgreSQL in production, SQLite in local dev/testing
if os.getenv('POSTGRES_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'estoque_db'),
            'USER': os.getenv('POSTGRES_USER', 'estoque_user'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'estoque_secret'),
            'HOST': os.getenv('POSTGRES_HOST', 'db'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS & CSRF Settings for api.estoquee.xyz
CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'False') == 'True' if not DEBUG else True

CORS_ALLOWED_ORIGINS = [
    'https://estoquee.xyz',
    'https://www.estoquee.xyz',
    'https://api.estoquee.xyz',
    'http://localhost:3000',
    'http://localhost:5173',
    'http://localhost:8000',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
]

extra_cors = os.getenv('CORS_ALLOWED_ORIGINS', '')
if extra_cors:
    CORS_ALLOWED_ORIGINS.extend([o.strip() for o in extra_cors.split(',') if o.strip()])

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.estoquee\.xyz$",
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'https://api.estoquee.xyz',
    'https://estoquee.xyz',
    'https://www.estoquee.xyz',
    'http://localhost:8000',
    'http://localhost:3000',
    'http://127.0.0.1:8000',
]

extra_csrf = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if extra_csrf:
    CSRF_TRUSTED_ORIGINS.extend([o.strip() for o in extra_csrf.split(',') if o.strip()])

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# DRF Spectacular / OpenAPI / Swagger Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Estoque Supply Chain & Escrow API',
    'DESCRIPTION': (
        'Comprehensive REST API for SMEs, suppliers, and retailers on Estoque. '
        'Connects off-chain inventory management, purchase orders, custody handovers, '
        'and Soroban smart-contract escrow payments in simulated USDC on Stellar Testnet.'
    ),
    'VERSION': '1.0.0',
    # Pin to a stable version without the import.meta bundle bug:
    'REDOC_DIST': 'https://cdn.jsdelivr.net/npm/redoc@2.1.5',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Authentication & Accounts', 'description': 'Supplier & Retailer authentication, registration and business profiles'},
        {'name': 'Inventory & Products', 'description': 'Product catalog, inventory batch registration, stock tracking and movements'},
        {'name': 'Purchase Orders', 'description': 'Purchase order lifecycle, dispatch, receipt, and inventory linking'},
        {'name': 'Soroban Blockchain & Escrow', 'description': 'Stellar Testnet Soroban smart contract interactions: batch proofs, custody handovers, USDC escrow funding, release and refunds'},
        {'name': 'Analytics & AI Insights', 'description': 'AI-assisted inventory optimization, reorder demand forecasts, and supply-chain metrics'},
    ],
}

# Redis & Celery
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_ALWAYS_EAGER', 'True') == 'True'

# Stellar & Soroban Config
STELLAR_NETWORK = os.getenv('STELLAR_NETWORK', 'TESTNET')
STELLAR_HORIZON_URL = os.getenv('STELLAR_HORIZON_URL', 'https://horizon-testnet.stellar.org')
SOROBAN_RPC_URL = os.getenv('SOROBAN_RPC_URL', 'https://soroban-testnet.stellar.org')
SOROBAN_CONTRACT_ID = os.getenv('SOROBAN_CONTRACT_ID', 'CAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD2KM')
TESTNET_USDC_ADDRESS = os.getenv('TESTNET_USDC_ADDRESS', 'CBIELTK6YBZJU5UP2WWQEUCYJLPU6QXN54CX7C3D57F7NUBJ7U2A2I5M')
SOROBAN_SIMULATION_MODE = os.getenv('SOROBAN_SIMULATION_MODE', 'True') == 'True'

