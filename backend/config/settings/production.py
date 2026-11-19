import os
from estoque_project.settings import *

# Production settings overrides
DEBUG = False

# Ensure allowed hosts include api.estoquee.xyz
if not os.getenv('DJANGO_ALLOWED_HOSTS'):
    ALLOWED_HOSTS = [
        'api.estoquee.xyz',
        'estoquee.xyz',
        'www.estoquee.xyz',
        '.estoquee.xyz',
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        'web',
    ]

# CSRF and Cookie security for HTTPS behind reverse proxy (Traefik)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

