"""
Django settings used when running tests.
"""

from copy import deepcopy

from django.utils.log import DEFAULT_LOGGING

from pds.settings import *

# ninja-extra logs every request on django.request at INFO/WARNING. That logger
# is absent from DEFAULT_LOGGING, so those lines propagate to the django
# console logger and clutter test output (including expected 4xx cases).
LOGGING = deepcopy(DEFAULT_LOGGING)
LOGGING["loggers"]["django.request"] = {
    "handlers": ["mail_admins"],
    "level": "ERROR",
    "propagate": False,
}
