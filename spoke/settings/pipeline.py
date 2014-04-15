import os
from .paths import PROJECT_ROOT, PARENT_DIR

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PARENT_DIR, 'collected_static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'web'),
)

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    #'pipeline.finders.PipelineFinder',
    #'pipeline.finders.CachedFileFinder',
)

# Compress the css and js using yui-compressor.
PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_COMPILERS = (
    'pipeline_compass.compass.CompassCompiler',
)
import speeches
PIPELINE_COMPASS_ARGUMENTS = '-I %s -r zurb-foundation' % os.path.join(speeches.__path__[0], 'static')

# On some platforms this might be called "yuicompressor", so it may be
# necessary to symlink it into your PATH as "yui-compressor".
PIPELINE_YUI_BINARY = '/usr/bin/env yui-compressor'

PIPELINE_CSS = {
    'sayit-default': {
        'source_filenames': (
            'sass/app.scss',
            'sass/speeches.scss',
        ),
        'output_filename': 'css/app.css',
    },
    'sayit-shakespeare': {
        'source_filenames': (
            'sass/app-shakespeare.scss',
            'sass/speeches-shakespeare.scss',
        ),
        'output_filename': 'css/app-shakespeare.css',
    },
}

PIPELINE_JS = {
    # Some things in document body (e.g. media player set up) call $()
    'sayit-default-head': {
        'source_filenames': (
            'speeches/js/jquery.js',
        ),
        'output_filename': 'js/sayit.head.min.js',
    },
    # The JS at the end of each page, before </body>
    'sayit-default': {
        'source_filenames': (
            'speeches/js/foundation/foundation.js',
            'speeches/js/foundation/foundation.dropdown.js',
            'javascripts/foundation/foundation.alerts.js',
            'speeches/js/speeches.js',
            # 'javascripts/vendor/jquery.text-effects.js',
        ),
        'output_filename': 'js/sayit.min.js',
    },
    # The media player
    'sayit-player': {
        'source_filenames': (
            'speeches/mediaelement/mediaelement-and-player.js',
        ),
        'output_filename': 'javascripts/sayit.mediaplayer.min.js',
    },
    'sayit-admin': {
        'source_filenames': (
            'speeches/js/jquery.js',
            'speeches/mediaelement/mediaelement-and-player.js',
            # "soundmanager2/script/soundmanager2.js"
        ),
        'output_filename': 'javascripts/sayit.admin.min.js',
    },
    'sayit-upload': {
        'source_filenames': (
            'speeches/js/jQuery-File-Upload/js/vendor/jquery.ui.widget.js',
            'speeches/js/jQuery-File-Upload/js/jquery.iframe-transport.js',
            'speeches/js/jQuery-File-Upload/js/jquery.fileupload.js',
            # "js/bootstrap-datepicker.js"
        ),
        'output_filename': 'javascripts/sayit.upload.min.js',
    },
}

