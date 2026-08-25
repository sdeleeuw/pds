from contacts.tests.api.contact.base import ContactAPITestCase


class ListContactsTests(ContactAPITestCase):
    async def test_list_returns_own_contacts(self):
        # Given: an authenticated user with an owned contact

        # When: listing contacts
        response = await self.request("get", "/", user=self.user)

        # Then: only that contact is returned
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.contact.id)
        self.assertEqual(data[0]["first_name"], "Jane")
        self.assertEqual(data[0]["last_name"], "Doe")
        self.assertEqual(data[0]["email"], "jane@example.com")
        self.assertEqual(data[0]["name"], "Jane Doe")

    async def test_list_excludes_other_users_contacts(self):
        # Given: contacts owned by the current user and another user

        # When: listing contacts as the current user
        response = await self.request("get", "/", user=self.user)

        # Then: only the current user's contacts are included
        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.json()}
        self.assertIn(self.contact.id, ids)
        self.assertNotIn(self.other_contact.id, ids)

    async def test_list_empty_for_user_without_contacts(self):
        # Given: an authenticated user with no contacts

        # When: listing contacts
        response = await self.request(
            "get",
            "/",
            user=self.user_without_contacts,
        )

        # Then: an empty list is returned
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    async def test_list_unauthenticated(self):
        # Given: no authenticated user

        # When: listing contacts
        response = await self.client.get("/contacts/")

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)
