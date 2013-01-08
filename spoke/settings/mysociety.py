# load the mySociety config from its special file

import sys
import yaml
from .paths import *

config = yaml.load(open(os.path.join(PROJECT_ROOT, 'conf', 'general.yml')))

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
if 'test' in sys.argv:
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'

TIME_ZONE = config.get('TIME_ZONE')
SECRET_KEY = config.get('DJANGO_SECRET_KEY')
GOOGLE_ANALYTICS_ACCOUNT = config.get('GOOGLE_ANALYTICS_ACCOUNT')

# PopIt instance to use for list of speakers
POPIT_INSTANCE = config.get('POPIT_INSTANCE')
POPIT_HOSTNAME = config.get('POPIT_HOSTNAME')
POPIT_API_VERSION = config.get('POPIT_API_VERSION')

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
SITE_TITLE = config.get('SITE_TITLE')
