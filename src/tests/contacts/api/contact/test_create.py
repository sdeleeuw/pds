from contacts.models import Contact
from tests.contacts.api.contact.base import ContactAPITestCase


class CreateContactTests(ContactAPITestCase):
    async def test_create_contact(self):
        # Given: an authenticated user and a full contact payload
        payload = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "mobile_phone": "+31600000001",
            "city": "London",
            "country": "GB",
            "date_of_birth": "1815-12-10",
            "notes": "Mathematician",
        }

        # When: creating a contact
        response = await self.request(
            "post",
            "/",
            user=self.user,
            json=payload,
        )

        # Then: the contact is created and owned by the user
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data["first_name"], "Ada")
        self.assertEqual(data["last_name"], "Lovelace")
        self.assertEqual(data["email"], "ada@example.com")
        self.assertEqual(data["name"], "Ada Lovelace")
        self.assertEqual(data["city"], "London")
        self.assertEqual(data["date_of_birth"], "1815-12-10")

        contact = await Contact.objects.aget(pk=data["id"])
        self.assertEqual(contact.owner_id, self.user.id)
        self.assertEqual(contact.email, "ada@example.com")

    async def test_create_contact_with_defaults(self):
        # Given: an authenticated user and a minimal payload

        # When: creating a contact with only a first name
        response = await self.request(
            "post",
            "/",
            user=self.user,
            json={"first_name": "Minimal"},
        )

        # Then: missing fields fall back to defaults
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data["first_name"], "Minimal")
        self.assertEqual(data["last_name"], "")
        self.assertEqual(data["email"], "")
        self.assertEqual(data["name"], "Minimal")
        self.assertIsNone(data["date_of_birth"])
        self.assertIsNone(data["age"])

    async def test_create_unauthenticated(self):
        # Given: no authenticated user

        # When: creating a contact
        response = await self.client.post(
            "/contacts/",
            json={"first_name": "Nope", "email": "nope@example.com"},
        )

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)
