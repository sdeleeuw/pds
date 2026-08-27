from tests.contacts.mcp.contact.base import ContactMCPTestCase


class ListContactsTests(ContactMCPTestCase):
    async def test_list_returns_own_contacts(self):
        # Given: an authenticated user with owned contacts

        # When: listing contacts
        result = await self.call_tool("list_contacts")

        # Then: only that user's contacts are returned
        self.assertFalse(result.is_error)

        data = self.contact_data(result)
        ids = {item["id"] for item in data}
        self.assertEqual(len(data), 3)
        self.assertIn(self.contact.id, ids)
        jane = next(item for item in data if item["id"] == self.contact.id)
        self.assertEqual(jane["first_name"], "Jane")
        self.assertEqual(jane["last_name"], "Doe")
        self.assertEqual(jane["email"], "jane@example.com")
        self.assertEqual(jane["name"], "Jane Doe")

    async def test_list_excludes_other_users_contacts(self):
        # Given: contacts owned by the current user and another user

        # When: listing contacts as the current user
        result = await self.call_tool("list_contacts")

        # Then: only the current user's contacts are included
        self.assertFalse(result.is_error)

        ids = {item["id"] for item in self.contact_data(result)}
        self.assertIn(self.contact.id, ids)
        self.assertNotIn(self.other_contact.id, ids)

    async def test_list_empty_for_user_without_contacts(self):
        # Given: an authenticated user with no contacts

        # When: listing contacts
        result = await self.call_tool(
            "list_contacts",
            user=self.user_without_contacts,
        )

        # Then: an empty list is returned
        self.assertFalse(result.is_error)
        self.assertEqual(self.contact_data(result), [])

    async def test_list_respects_limit(self):
        # Given: more owned contacts than the requested limit

        # When: listing with a limit of 1
        result = await self.call_tool("list_contacts", {"limit": 1})

        # Then: at most one contact is returned
        self.assertFalse(result.is_error)
        self.assertEqual(len(self.contact_data(result)), 1)

    async def test_list_unauthenticated(self):
        # Given: no authenticated user

        # When: listing contacts
        result = await self.call_tool("list_contacts", user=None)

        # Then: the call fails
        self.assertTrue(result.is_error)
