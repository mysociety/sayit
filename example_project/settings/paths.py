import os

# Path to here is something like
# /data/vhost/<vhost>/<repo>/<project_name>/settings/base.py
SETTINGS_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))
PROJECT_ROOT = os.path.abspath(os.path.join(PROJECT_DIR, '..'))
PARENT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, '..'))
