from contacts.tests.mcp.contact.base import ContactMCPTestCase


class UpdateContactTests(ContactMCPTestCase):
    async def test_update_contact(self):
        # Given: a contact owned by the authenticated user

        # When: patching several fields
        result = await self.call_tool(
            "update_contact",
            {
                "contact_id": self.contact.id,
                "payload": {
                    "first_name": "Janet",
                    "city": "Rotterdam",
                    "notes": "Updated notes",
                },
            },
        )

        # Then: those fields are updated and persisted
        self.assertFalse(result.is_error)

        data = self.contact_data(result)
        self.assertEqual(data["first_name"], "Janet")
        self.assertEqual(data["last_name"], "Doe")
        self.assertEqual(data["city"], "Rotterdam")
        self.assertEqual(data["notes"], "Updated notes")
        self.assertEqual(data["name"], "Janet Doe")

        await self.contact.arefresh_from_db()
        self.assertEqual(self.contact.first_name, "Janet")
        self.assertEqual(self.contact.city, "Rotterdam")
        self.assertEqual(self.contact.notes, "Updated notes")

    async def test_update_partial_fields_only(self):
        # Given: a contact owned by the authenticated user

        # When: patching only the email
        result = await self.call_tool(
            "update_contact",
            {
                "contact_id": self.contact.id,
                "payload": {"email": "janet.doe@example.com"},
            },
        )

        # Then: only the email changes
        self.assertFalse(result.is_error)

        data = self.contact_data(result)
        self.assertEqual(data["email"], "janet.doe@example.com")
        self.assertEqual(data["first_name"], "Jane")
        self.assertEqual(data["last_name"], "Doe")

    async def test_update_other_users_contact_returns_error(self):
        # Given: a contact owned by another user

        # When: patching that contact as the current user
        result = await self.call_tool(
            "update_contact",
            {
                "contact_id": self.other_contact.id,
                "payload": {"first_name": "Hacked"},
            },
        )

        # Then: the contact is not found and remains unchanged
        self.assertTrue(result.is_error)

        await self.other_contact.arefresh_from_db()
        self.assertEqual(self.other_contact.first_name, "John")

    async def test_update_missing_contact_returns_error(self):
        # Given: an authenticated user and a non-existent contact id

        # When: patching that contact
        result = await self.call_tool(
            "update_contact",
            {"contact_id": 999999, "payload": {"first_name": "Ghost"}},
        )

        # Then: the contact is not found
        self.assertTrue(result.is_error)

    async def test_update_duplicate_email_returns_error(self):
        # Given: the user already owns a second contact with a different email

        # When: changing that contact to the first contact's email
        result = await self.call_tool(
            "update_contact",
            {
                "contact_id": self.second_contact.id,
                "payload": {"email": "jane@example.com"},
            },
        )

        # Then: the call fails with an actionable error
        self.assertTrue(result.is_error)

    async def test_update_unauthenticated(self):
        # Given: an existing contact and no authenticated user

        # When: patching that contact
        result = await self.call_tool(
            "update_contact",
            {
                "contact_id": self.contact.id,
                "payload": {"first_name": "Nope"},
            },
            user=None,
        )

        # Then: the call fails
        self.assertTrue(result.is_error)
