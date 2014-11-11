SOUTH_ERROR_MESSAGE = """\n
For South support, make sure you have South 1.0 installed, or
customize the SOUTH_MIGRATION_MODULES setting like so:

    SOUTH_MIGRATION_MODULES = {
        'speeches': 'speeches.south_migrations',
    }
"""

try:  # Django < 1.7
    from django.db import migrations # noqa
except ImportError:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(SOUTH_ERROR_MESSAGE)
