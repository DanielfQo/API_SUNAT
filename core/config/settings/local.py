from .base import *  # noqa: F401, F403


DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Permitir todos los orígenes localmente para facilitar el desarrollo del frontend
CORS_ALLOW_ALL_ORIGINS = True

# Habilitar la API navegable de DRF en desarrollo
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]