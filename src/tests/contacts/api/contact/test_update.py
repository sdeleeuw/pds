from tests.contacts.api.contact.base import ContactAPITestCase


class UpdateContactTests(ContactAPITestCase):
    async def test_update_contact(self):
        # Given: a contact owned by the authenticated user

        # When: patching several fields
        response = await self.request(
            "patch",
            f"/{self.contact.id}/",
            user=self.user,
            json={
                "first_name": "Janet",
                "city": "Rotterdam",
                "notes": "Updated notes",
            },
        )

        # Then: those fields are updated and persisted
        self.assertEqual(response.status_code, 200)

        data = response.json()
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
        response = await self.request(
            "patch",
            f"/{self.contact.id}/",
            user=self.user,
            json={"email": "janet.doe@example.com"},
        )

        # Then: only the email changes
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["email"], "janet.doe@example.com")
        self.assertEqual(data["first_name"], "Jane")
        self.assertEqual(data["last_name"], "Doe")

    async def test_update_other_users_contact_returns_404(self):
        # Given: a contact owned by another user

        # When: patching that contact as the current user
        response = await self.request(
            "patch",
            f"/{self.other_contact.id}/",
            user=self.user,
            json={"first_name": "Hacked"},
        )

        # Then: the contact is not found and remains unchanged
        self.assertEqual(response.status_code, 404)

        await self.other_contact.arefresh_from_db()

        self.assertEqual(self.other_contact.first_name, "John")

    async def test_update_missing_contact_returns_404(self):
        # Given: an authenticated user and a non-existent contact id

        # When: patching that contact
        response = await self.request(
            "patch",
            "/999999/",
            user=self.user,
            json={"first_name": "Ghost"},
        )

        # Then: the contact is not found
        self.assertEqual(response.status_code, 404)

    async def test_update_unauthenticated(self):
        # Given: an existing contact and no authenticated user

        # When: patching that contact
        response = await self.client.patch(
            f"/contacts/{self.contact.id}/",
            json={"first_name": "Nope"},
        )

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)
