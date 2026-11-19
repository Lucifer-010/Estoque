import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-estoque-prod-test-key-592837418293')

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True

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
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
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

