"""
Django settings used when running tests.
"""

from copy import deepcopy
from logging import Filter, LogRecord

from django.utils.log import DEFAULT_LOGGING

from pds.settings import *  # noqa: F403


class _SilenceNinjaJWTValidationNoise(Filter):
    """Drop ninja_jwt's expected ERROR when a schema raises ValidationError."""

    def filter(self, record: LogRecord) -> bool:
        return "raised exception" not in record.getMessage()


DEBUG = True
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# ninja-extra logs every request on django.request at INFO/WARNING. That logger
# is absent from DEFAULT_LOGGING, so those lines propagate to the django
# console logger and clutter test output (including expected 4xx cases).
LOGGING = deepcopy(DEFAULT_LOGGING)
LOGGING["filters"] = {
    **LOGGING.get("filters", {}),
    "silence_ninja_jwt_validation": {
        "()": "pds.settings_test._SilenceNinjaJWTValidationNoise",
    },
}
LOGGING["loggers"]["django.request"] = {
    "handlers": ["mail_admins"],
    "level": "ERROR",
    "propagate": False,
}
LOGGING["loggers"]["django"] = {
    **LOGGING["loggers"].get("django", {}),
    "filters": ["silence_ninja_jwt_validation"],
}
