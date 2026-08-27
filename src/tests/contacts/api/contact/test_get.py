from tests.contacts.api.contact.base import ContactAPITestCase


class GetContactTests(ContactAPITestCase):
    async def test_get_own_contact(self):
        # Given: a contact owned by the authenticated user

        # When: fetching that contact
        response = await self.request(
            "get",
            f"/{self.contact.id}/",
            user=self.user,
        )

        # Then: the contact details are returned
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["id"], self.contact.id)
        self.assertEqual(data["first_name"], "Jane")
        self.assertEqual(data["last_name"], "Doe")
        self.assertEqual(data["email"], "jane@example.com")
        self.assertEqual(data["name"], "Jane Doe")
        self.assertEqual(data["city"], "Amsterdam")
        self.assertEqual(data["date_of_birth"], "1990-05-15")
        self.assertIsNotNone(data["age"])

    async def test_get_other_users_contact_returns_404(self):
        # Given: a contact owned by another user

        # When: fetching that contact as the current user
        response = await self.request(
            "get",
            f"/{self.other_contact.id}/",
            user=self.user,
        )

        # Then: the contact is not found
        self.assertEqual(response.status_code, 404)

    async def test_get_missing_contact_returns_404(self):
        # Given: an authenticated user and a non-existent contact id

        # When: fetching that contact
        response = await self.request("get", "/999999/", user=self.user)

        # Then: the contact is not found
        self.assertEqual(response.status_code, 404)

    async def test_get_unauthenticated(self):
        # Given: an existing contact and no authenticated user

        # When: fetching that contact
        response = await self.client.get(f"/contacts/{self.contact.id}/")

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)
