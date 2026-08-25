from contacts.tests.fixtures import create_contact
from contacts.tests.mcp.contact.base import ContactMCPTestCase


class SearchContactsTests(ContactMCPTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        create_contact(
            owner=cls.user,
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            city="London",
        )

    async def test_search_by_name(self):
        # Given: multiple owned contacts

        # When: searching by last name
        result = await self.call_tool("search_contacts", {"query": "Lovelace"})

        # Then: only matching contacts are returned
        self.assertFalse(result.is_error)
        data = self.contact_data(result)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["first_name"], "Ada")
        self.assertEqual(data[0]["email"], "ada@example.com")

    async def test_search_by_city(self):
        # Given: a contact in Amsterdam and another in London

        # When: searching by city
        result = await self.call_tool("search_contacts", {"query": "Amsterdam"})

        # Then: the Amsterdam contact is returned
        self.assertFalse(result.is_error)
        data = self.contact_data(result)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.contact.id)

    async def test_search_excludes_other_users_contacts(self):
        # Given: another user owns a contact matching the query

        # When: searching as the current user
        result = await self.call_tool("search_contacts", {"query": "Smith"})

        # Then: other users' contacts are not included
        self.assertFalse(result.is_error)
        self.assertEqual(self.contact_data(result), [])

    async def test_search_unauthenticated(self):
        # Given: no authenticated user

        # When: searching contacts
        result = await self.call_tool(
            "search_contacts",
            {"query": "Jane"},
            user=None,
        )

        # Then: the call fails
        self.assertTrue(result.is_error)
