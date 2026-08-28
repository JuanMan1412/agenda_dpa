# Agregar/ajustar esto en settings.py del proyecto Django

INSTALLED_APPS = [
    # ... apps por defecto de Django ...
    "rest_framework",
    "corsheaders",
    "agenda",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # debe ir arriba de CommonMiddleware
    # ... resto del middleware ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # puerto default de Vite
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "TU_BASE",
        "USER": "TU_USUARIO",
        "PASSWORD": "TU_PASSWORD",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        # agregá acá su esquema real (TokenAuth / JWT) para el
        # personal de mesa de entradas que usa React
    ],
}

# Claves de la(s) aplicación(es) externa(s) autorizadas a reservar
# número. Generen una clave larga y random por cada sistema externo.
AGENDA_API_KEYS = {
    "REEMPLAZAR-POR-UNA-CLAVE-LARGA-Y-SECRETA": "sistema_expedientes",
}
