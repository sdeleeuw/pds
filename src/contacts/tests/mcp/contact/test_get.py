from contacts.tests.mcp.contact.base import ContactMCPTestCase


class GetContactTests(ContactMCPTestCase):
    async def test_get_own_contact(self):
        # Given: a contact owned by the authenticated user

        # When: fetching that contact
        result = await self.call_tool(
            "get_contact",
            {"contact_id": self.contact.id},
        )

        # Then: the contact details are returned
        self.assertFalse(result.is_error)

        data = self.contact_data(result)
        self.assertEqual(data["id"], self.contact.id)
        self.assertEqual(data["first_name"], "Jane")
        self.assertEqual(data["last_name"], "Doe")
        self.assertEqual(data["email"], "jane@example.com")
        self.assertEqual(data["name"], "Jane Doe")
        self.assertEqual(data["city"], "Amsterdam")
        self.assertEqual(data["date_of_birth"], "1990-05-15")
        self.assertIsNotNone(data["age"])

    async def test_get_other_users_contact_returns_error(self):
        # Given: a contact owned by another user

        # When: fetching that contact as the current user
        result = await self.call_tool(
            "get_contact",
            {"contact_id": self.other_contact.id},
        )

        # Then: the contact is not found
        self.assertTrue(result.is_error)

    async def test_get_missing_contact_returns_error(self):
        # Given: an authenticated user and a non-existent contact id

        # When: fetching that contact
        result = await self.call_tool("get_contact", {"contact_id": 999999})

        # Then: the contact is not found
        self.assertTrue(result.is_error)

    async def test_get_unauthenticated(self):
        # Given: an existing contact and no authenticated user

        # When: fetching that contact
        result = await self.call_tool(
            "get_contact",
            {"contact_id": self.contact.id},
            user=None,
        )

        # Then: the call fails
        self.assertTrue(result.is_error)
