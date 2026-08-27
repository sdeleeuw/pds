import logging

from django.test import TestCase
from ninja.testing import TestAsyncClient

from pds.tests.fixtures import create_user
from pds.urls import api


class _SilenceNinjaJWTValidationNoise(logging.Filter):
    """Drop ninja_jwt's expected ERROR when a schema raises ValidationError."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "raised exception" not in record.getMessage()


class AuthAPITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(username="alice", email="alice@example.com")

        cls.inactive_user = create_user(
            username="inactive",
            email="inactive@example.com",
        )
        cls.inactive_user.is_active = False
        cls.inactive_user.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._django_logger = logging.getLogger("django")
        cls._jwt_noise_filter = _SilenceNinjaJWTValidationNoise()
        cls._django_logger.addFilter(cls._jwt_noise_filter)

    @classmethod
    def tearDownClass(cls):
        cls._django_logger.removeFilter(cls._jwt_noise_filter)
        super().tearDownClass()

    def setUp(self):
        self.client = TestAsyncClient(api)

    async def request(self, method: str, path: str, **kwargs):
        return await getattr(self.client, method)(f"/auth{path}", **kwargs)
