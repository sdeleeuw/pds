from contacts.models import Contact
from tests.contacts.mcp.contact.base import ContactMCPTestCase


class DeleteContactTests(ContactMCPTestCase):
    async def test_delete_contact(self):
        # Given: a contact owned by the authenticated user
        contact_id = self.contact.id

        # When: deleting that contact
        result = await self.call_tool(
            "delete_contact",
            {"contact_id": contact_id},
        )

        # Then: the contact is removed
        self.assertFalse(result.is_error)
        self.assertFalse(await Contact.objects.filter(pk=contact_id).aexists())

    async def test_delete_other_users_contact_returns_error(self):
        # Given: a contact owned by another user

        # When: deleting that contact as the current user
        result = await self.call_tool(
            "delete_contact",
            {"contact_id": self.other_contact.id},
        )

        # Then: the contact is not found and remains unchanged
        self.assertTrue(result.is_error)
        self.assertTrue(
            await Contact.objects.filter(pk=self.other_contact.id).aexists()
        )

    async def test_delete_missing_contact_returns_error(self):
        # Given: an authenticated user and a non-existent contact id

        # When: deleting that contact
        result = await self.call_tool("delete_contact", {"contact_id": 999999})

        # Then: the contact is not found
        self.assertTrue(result.is_error)

    async def test_delete_unauthenticated(self):
        # Given: an existing contact and no authenticated user

        # When: deleting that contact
        result = await self.call_tool(
            "delete_contact",
            {"contact_id": self.contact.id},
            user=None,
        )

        # Then: the call fails and the contact remains
        self.assertTrue(result.is_error)
        self.assertTrue(await Contact.objects.filter(pk=self.contact.id).aexists())
