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
