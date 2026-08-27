from django.test import TestCase
from ninja.testing import TestAsyncClient

from tests.fixtures import create_user
from pds.urls import api


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

    def setUp(self):
        self.client = TestAsyncClient(api)

    async def request(self, method: str, path: str, **kwargs):
        return await getattr(self.client, method)(f"/auth{path}", **kwargs)
