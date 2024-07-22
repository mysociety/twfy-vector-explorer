"""
Helper import to setup django correctly for jupyter notebooks
Needs to be imported before importing models.
"""

import os

import django

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ["DJANGO_SETTINGS_MODULE"] = "twfy_vector_explorer.settings"
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Initialize Django
django.setup()
