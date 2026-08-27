from django.test import TestCase
from mcp import Client

from tests.fixtures import create_contact, create_user
from tests.pds.mcp.auth.helpers import authenticated_as

_UNSET = object()


class ContactMCPTestCase(TestCase):
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

        cls.second_contact = create_contact(
            owner=cls.user,
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            city="London",
        )

        cls.third_contact = create_contact(
            owner=cls.user,
            first_name="Jane",
            last_name="Second",
            email="jane.second@example.com",
            city="Amsterdam",
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

    async def call_tool(self, name: str, arguments: dict | None = None, *, user=_UNSET):
        from pds.mcp.server import mcp

        if user is _UNSET:
            user = self.user

        async with Client(mcp, raise_exceptions=True) as client:
            if user is None:
                return await client.call_tool(name, arguments or {})

            with authenticated_as(user):
                return await client.call_tool(name, arguments or {})

    def contact_data(self, result) -> dict | list:
        data = result.structured_content

        if isinstance(data, dict) and "result" in data and len(data) == 1:
            return data["result"]

        return data
