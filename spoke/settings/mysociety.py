# load the mySociety config from its special file

import sys
import yaml
from .paths import *

from django.core.exceptions import ImproperlyConfigured

config_file = os.path.join(PROJECT_ROOT, 'conf', 'general.yml')
with open(config_file) as f:
    config = yaml.load(f)

DEBUG = bool(int(config.get('STAGING')))
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config.get('SAYIT_DB_NAME'),
        'USER': config.get('SAYIT_DB_USER'),
        'PASSWORD': config.get('SAYIT_DB_PASS'),
        'HOST': config.get('SAYIT_DB_HOST'),
        'PORT': config.get('SAYIT_DB_PORT'),
    }
}

TIME_ZONE = config.get('TIME_ZONE')
SECRET_KEY = config.get('DJANGO_SECRET_KEY')
GOOGLE_ANALYTICS_ACCOUNT = config.get('GOOGLE_ANALYTICS_ACCOUNT')

BASE_HOST = config.get('BASE_HOST')
if BASE_HOST is None:
    raise ImproperlyConfigured, "BASE_HOST must be defined in %s" % (config_file,)
BASE_PORT = config.get('BASE_PORT')


# AT&T api details
ATT_OAUTH_URL = config.get('ATT_OAUTH_URL')
ATT_CLIENT_ID = config.get('ATT_CLIENT_ID')
ATT_SECRET = config.get('ATT_SECRET')
ATT_API_URL = config.get('ATT_API_URL')
# How long to wait for the api before timing out
ATT_TIMEOUT = config.get('ATT_TIMEOUT')

# Celery Broker details
BROKER_URL = config.get('CELERY_BROKER_URL')

# Content formatting
# How many characters of speech text to show
SPEECH_SUMMARY_LENGTH = config.get('SPEECH_SUMMARY_LENGTH')
# Default auto-transcription text
DEFAULT_TRANSCRIPTION = config.get('DEFAULT_TRANSCRIPTION')
