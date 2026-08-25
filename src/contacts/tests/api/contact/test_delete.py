from contacts.models import Contact
from contacts.tests.api.contact.base import ContactAPITestCase


class DeleteContactTests(ContactAPITestCase):
    async def test_delete_contact(self):
        # Given: a contact owned by the authenticated user
        contact_id = self.contact.id

        # When: deleting that contact
        response = await self.request(
            "delete",
            f"/{contact_id}/",
            user=self.user,
        )

        # Then: the contact is removed
        self.assertEqual(response.status_code, 204)
        self.assertFalse(await Contact.objects.filter(pk=contact_id).aexists())

    async def test_delete_other_users_contact_returns_404(self):
        # Given: a contact owned by another user

        # When: deleting that contact as the current user
        response = await self.request(
            "delete",
            f"/{self.other_contact.id}/",
            user=self.user,
        )

        # Then: the contact is not found and remains unchanged
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            await Contact.objects.filter(pk=self.other_contact.id).aexists()
        )

    async def test_delete_missing_contact_returns_404(self):
        # Given: an authenticated user and a non-existent contact id

        # When: deleting that contact
        response = await self.request("delete", "/999999/", user=self.user)

        # Then: the contact is not found
        self.assertEqual(response.status_code, 404)

    async def test_delete_unauthenticated(self):
        # Given: an existing contact and no authenticated user

        # When: deleting that contact
        response = await self.client.delete(f"/contacts/{self.contact.id}/")

        # Then: the request is rejected and the contact remains
        self.assertEqual(response.status_code, 401)
        self.assertTrue(await Contact.objects.filter(pk=self.contact.id).aexists())
