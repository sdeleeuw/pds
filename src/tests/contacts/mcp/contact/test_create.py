from contacts.models import Contact
from tests.contacts.mcp.contact.base import ContactMCPTestCase


class CreateContactTests(ContactMCPTestCase):
    async def test_create_contact(self):
        # Given: an authenticated user and a full contact payload
        payload = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "created.ada@example.com",
            "mobile_phone": "+31600000001",
            "city": "London",
            "country": "GB",
            "date_of_birth": "1815-12-10",
            "notes": "Mathematician",
        }

        # When: creating a contact
        result = await self.call_tool("create_contact", {"payload": payload})

        # Then: the contact is created and owned by the user
        self.assertFalse(result.is_error)

        data = self.contact_data(result)
        self.assertEqual(data["first_name"], "Ada")
        self.assertEqual(data["last_name"], "Lovelace")
        self.assertEqual(data["email"], "created.ada@example.com")
        self.assertEqual(data["name"], "Ada Lovelace")
        self.assertEqual(data["city"], "London")
        self.assertEqual(data["date_of_birth"], "1815-12-10")

        contact = await Contact.objects.aget(pk=data["id"])
        self.assertEqual(contact.owner_id, self.user.id)
        self.assertEqual(contact.email, "created.ada@example.com")

    async def test_create_contact_with_defaults(self):
        # Given: an authenticated user and a minimal payload

        # When: creating a contact with only a first name
        result = await self.call_tool(
            "create_contact",
            {"payload": {"first_name": "Minimal"}},
        )

        # Then: missing fields fall back to defaults
        self.assertFalse(result.is_error)

        data = self.contact_data(result)
        self.assertEqual(data["first_name"], "Minimal")
        self.assertEqual(data["last_name"], "")
        self.assertEqual(data["email"], "")
        self.assertEqual(data["name"], "Minimal")
        self.assertIsNone(data["date_of_birth"])
        self.assertIsNone(data["age"])

    async def test_create_duplicate_email_returns_error(self):
        # Given: the user already owns a contact with this email

        # When: creating another contact with the same email
        result = await self.call_tool(
            "create_contact",
            {"payload": {"first_name": "Copy", "email": "jane@example.com"}},
        )

        # Then: the call fails with an actionable error
        self.assertTrue(result.is_error)

    async def test_create_multiple_blank_emails(self):
        # Given: an authenticated user

        # When: creating two contacts without an email
        first = await self.call_tool(
            "create_contact",
            {"payload": {"first_name": "BlankOne"}},
        )
        second = await self.call_tool(
            "create_contact",
            {"payload": {"first_name": "BlankTwo"}},
        )

        # Then: both succeed
        self.assertFalse(first.is_error)
        self.assertFalse(second.is_error)

    async def test_create_same_email_for_other_owner(self):
        # Given: another user already has a contact with this email

        # When: creating a contact with the same email as the current user
        result = await self.call_tool(
            "create_contact",
            {"payload": {"first_name": "AlsoJohn", "email": "john@example.com"}},
        )

        # Then: the contact is created because uniqueness is per owner
        self.assertFalse(result.is_error)
        self.assertEqual(self.contact_data(result)["email"], "john@example.com")

    async def test_create_unauthenticated(self):
        # Given: no authenticated user

        # When: creating a contact
        result = await self.call_tool(
            "create_contact",
            {"payload": {"first_name": "Nope", "email": "nope@example.com"}},
            user=None,
        )

        # Then: the call fails
        self.assertTrue(result.is_error)
