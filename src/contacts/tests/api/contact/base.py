from django.test import TestCase
from ninja.testing import TestAsyncClient
from ninja_jwt.tokens import RefreshToken

from contacts.tests.fixtures import create_contact, create_user
from pds.urls import api


class ContactAPITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(
            username="alice",
            email="alice@example.com",
        )

        cls.other_user = create_user(
            username="bob",
            email="bob@example.com",
        )

        cls.contact = create_contact(
            owner=cls.user,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
        )

        cls.other_contact = create_contact(
            owner=cls.other_user,
            first_name="John",
            last_name="Smith",
            email="john@example.com",
        )

        cls.user_without_contacts = create_user(
            username="carol",
            email="carol@example.com",
        )

    def setUp(self):
        self.client = TestAsyncClient(api)

    async def request(self, method: str, path: str, user=None, **kwargs):
        request_params = dict(kwargs)

        if user is not None:
            access_token = str(RefreshToken.for_user(user).access_token)
            headers = dict(request_params.pop("headers", {}))
            headers["Authorization"] = f"Bearer {access_token}"
            request_params["headers"] = headers

        return await getattr(self.client, method)(
            f"/contacts{path}",
            **request_params,
        )
