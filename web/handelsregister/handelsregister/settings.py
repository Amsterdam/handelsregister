"""
Django settings for handelsregister project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""
import os
import re
import sys

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Handelsregister
SCOPE_HR_R = 'HR/R'


def get_docker_host():
    """
    Looks for the DOCKER_HOST environment variable to find the VM
    running docker-machine.

    If the environment variable is not found, it is assumed that
    you're running docker on localhost.
    """
    d_host = os.getenv('DOCKER_HOST', None)
    if d_host:
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', d_host):
            return d_host

        return re.match(r'tcp://(.*?):\d+', d_host).group(1)
    return 'localhost'


# noinspection PyBroadException
def in_docker():
    """
    Checks pid 1 cgroup settings to check with reasonable certainty we're in a
    docker env.
    :return: true when running in a docker container, false otherwise
    """
    try:
        cgroup = open('/proc/1/cgroup', 'r').read()
        return ':/docker/' in cgroup or ':/docker-ce/' in cgroup
    except:
        return False


OVERRIDE_HOST_ENV_VAR = 'DATABASE_HOST_OVERRIDE'
OVERRIDE_PORT_ENV_VAR = 'DATABASE_PORT_OVERRIDE'

OVERRIDE_EL_HOST_VAR = 'ELASTIC_HOST_OVERRIDE'
OVERRIDE_EL_PORT_VAR = 'ELASTIC_PORT_OVERRIDE'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LocationKey:
    local = 'local'
    docker = 'docker'
    override = 'override'


def get_database_key():
    if os.getenv(OVERRIDE_HOST_ENV_VAR):
        return LocationKey.override
    elif in_docker():
        return LocationKey.docker

    return LocationKey.local


DATABASE_OPTIONS = {
    LocationKey.docker: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'handelsregister'),
        'USER': os.getenv('DATABASE_USER', 'handelsregister'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': 'database',
        'PORT': '5432',
        'CONN_MAX_AGE': 5,
    },
    LocationKey.local: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'handelsregister'),
        'USER': os.getenv('DATABASE_USER', 'handelsregister'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': get_docker_host(),
        'PORT': '5406',
        'CONN_MAX_AGE': 5,
    },
    LocationKey.override: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'handelsregister'),
        'USER': os.getenv('DATABASE_USER', 'handelsregister'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': os.getenv(OVERRIDE_HOST_ENV_VAR),
        'PORT': os.getenv(OVERRIDE_PORT_ENV_VAR, '5432'),
        'CONN_MAX_AGE': 5,
    },
}

DATABASES = {
    'default': DATABASE_OPTIONS[get_database_key()]
}

VBO_URI = os.getenv('BAG_API_ROOT', 'https://api.data.amsterdam.nl/bag/v1.1') + "/verblijfsobject/"

DATAPUNT_API_REQUEST_HEADER = os.getenv('DATAPUNT_API_REQUEST_HEADER', 'e1d3b888-fd6a-4be8-ad96-0d63b4aa7982')
# SECURITY WARNING: keep the secret key used in production secret!
insecure_key = 'insecure'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', insecure_key)
DEBUG = SECRET_KEY == insecure_key
DEBUG = False

ALLOWED_HOSTS = ['*']

PARTIAL_IMPORT = {
    'numerator': 0,
    'denominator': 1,
}


DATAPUNT_API_URL = os.getenv(
    # note the ending /
    'DATAPUNT_API_URL', 'https://api.data.amsterdam.nl/')


# Application definition
INSTALLED_APPS = [
    'datapunt_api',
    'handelsregister',
    'datasets.kvkdump',
    'datasets.hr',
    'datasets.sbicodes',
    'geo_views',

    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django_filters',

    'django_extensions',

    'django.contrib.gis',
    'rest_framework',
    'rest_framework_gis',
    'drf_yasg',

]

INTERNAL_IPS = ('127.0.0.1', '0.0.0.0')

MIDDLEWARE = [
    'authorization_django.authorization_middleware',
]

if DEBUG:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE += (
        'corsheaders.middleware.CorsMiddleware',
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
    CORS_ORIGIN_ALLOW_ALL = True


ROOT_URLCONF = 'handelsregister.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'handelsregister.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DUMP_DIR = 'mks-dump'

ELK_PORT = os.getenv(OVERRIDE_EL_PORT_VAR, '9200')

ELASTIC_OPTIONS = {
    LocationKey.docker: ["http://elasticsearch:9200"],
    LocationKey.local: [f"http://{get_docker_host()}:9200"],
    LocationKey.override: [
        f"http://{os.getenv(OVERRIDE_EL_HOST_VAR)}:{ELK_PORT}"],    # noqa
}
ELASTIC_SEARCH_HOSTS = ELASTIC_OPTIONS[get_database_key()]

ELASTIC_INDICES = {
    'HR': 'handelsregister',
}

PARTIAL_IMPORT = {
    'numerator': 0,
    'denominator': 1,
}

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
if TESTING:
    for k, v in ELASTIC_INDICES.items():
        ELASTIC_INDICES[k] += 'test'

BATCH_SETTINGS = dict(
    batch_size=4000
)

REST_FRAMEWORK = dict(
    PAGE_SIZE=100,
    DATETIME_FORMAT=('%d-%m-%Y'),

    UNAUTHENTICATED_USER=None,
    UNAUTHENTICATED_TOKEN=None,

    MAX_PAGINATE_BY=100,
    DEFAULT_PAGINATION_CLASS='drf_hal_json.pagination.HalPageNumberPagination',
    DEFAULT_PARSER_CLASSES=('drf_hal_json.parsers.JsonHalParser',),
    DEFAULT_RENDERER_CLASSES=(
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer'
    ),
    DEFAULT_FILTER_BACKENDS=(
        'django_filters.rest_framework.DjangoFilterBackend',
        # 'rest_framework.filters.OrderingFilter',

    ),
    COERCE_DECIMAL_TO_STRING=True,
)


auth_url = ""
if os.getenv('KEYCLOAK_JWKS_URL'):
    auth_url = "/".join(os.getenv('KEYCLOAK_JWKS_URL').rsplit('/')[0:-1]) + "/auth"

SWAGGER_SETTINGS = {
    'VALIDATOR_URL': None,
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'oauth2': {
            'type': 'oauth2',
            'authorizationUrl': auth_url,
            'flow': 'accessCode',
            'scopes': {
                SCOPE_HR_R: "Toegang HR",
            }
        }
    },
    'OAUTH2_CONFIG': {
      'clientId': 'datadiensten-swagger-ui',
      'appName': 'handelsregister'
   }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/handelsregister/static/'

STATIC_ROOT = '/static/'

HEALTH_MODEL = 'hr.MaatschappelijkeActiviteit'

LOGSTASH_HOST = os.getenv('LOGSTASH_HOST', '127.0.0.1')
LOGSTASH_PORT = int(os.getenv('LOGSTASH_GELF_UDP_PORT', 12201))

# The following JWKS data was obtained in the authz project :  jwkgen -create -alg ES256
# This is a test public/private key def and added for testing.
JWKS_TEST_KEY = """
    {
        "keys": [
            {
                "kty": "EC",
                "key_ops": [
                    "verify",
                    "sign"
                ],
                "kid": "2aedafba-8170-4064-b704-ce92b7c89cc6",
                "crv": "P-256",
                "x": "6r8PYwqfZbq_QzoMA4tzJJsYUIIXdeyPA27qTgEJCDw=",
                "y": "Cf2clfAfFuuCB06NMfIat9ultkMyrMQO9Hd2H7O9ZVE=",
                "d": "N1vu0UQUp0vLfaNeM0EDbl4quvvL6m_ltjoAXXzkI3U="
            }
        ]
    }
"""


# Security
DATAPUNT_AUTHZ = {
    'JWKS': os.getenv('PUB_JWKS', JWKS_TEST_KEY),
    'JWKS_URL': os.getenv('KEYCLOAK_JWKS_URL'),
    'MIN_SCOPE': SCOPE_HR_R,
    'FORCED_ANONYMOUS_ROUTES': ('/status/', '/handelsregister/static/', '/handelsregister/docs/'),
    # 'ALWAYS_OK': True,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'console': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },

        'graypy': {
            'level': 'ERROR',
            'class': 'graypy.GELFHandler',
            'host': LOGSTASH_HOST,
            'port': LOGSTASH_PORT,
        },

    },

    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'graypy'],
    },

    'loggers': {
        'django.db': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
        },

        'datasets.hr.improve_location_with_search': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        # Debug all batch jobs
        'doc': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'index': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'search': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

        'elasticsearch': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

        'urllib3': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

        'factory.containers': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },

        'factory.generate': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },

        'requests.packages.urllib3.connectionpool': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

        # Log all unhandled exceptions
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

    },
}

SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment="handelsregister",
        integrations=[DjangoIntegration()]
    )
