from tests.pds.api.auth.base import AuthAPITestCase


class ObtainTokenTests(AuthAPITestCase):
    async def test_obtain_token_with_valid_credentials(self):
        # Given: an active user with a known password

        # When: posting valid credentials
        response = await self.request(
            "post",
            "/pair",
            json={"username": "alice", "password": "password"},
        )

        # Then: access and refresh tokens are returned along with the username
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["username"], "alice")
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertIsInstance(data["access"], str)
        self.assertIsInstance(data["refresh"], str)
        self.assertGreater(len(data["access"]), 0)
        self.assertGreater(len(data["refresh"]), 0)

    async def test_obtain_token_with_invalid_password(self):
        # Given: an active user

        # When: posting credentials with a wrong password
        response = await self.request(
            "post",
            "/pair",
            json={"username": "alice", "password": "wrong-password"},
        )

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)

    async def test_obtain_token_with_unknown_user(self):
        # Given: no user with the requested username

        # When: posting credentials for a non-existent user
        response = await self.request(
            "post",
            "/pair",
            json={"username": "ghost", "password": "password"},
        )

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)

    async def test_obtain_token_with_inactive_user(self):
        # Given: a deactivated user

        # When: posting the user's credentials
        response = await self.request(
            "post",
            "/pair",
            json={"username": "inactive", "password": "password"},
        )

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)

    async def test_obtain_token_with_missing_password(self):
        # Given: a user exists

        # When: posting credentials without a password
        response = await self.request(
            "post",
            "/pair",
            json={"username": "alice"},
        )

        # Then: the request is rejected with a validation error
        self.assertEqual(response.status_code, 400)

    async def test_obtain_token_with_missing_username(self):
        # Given: nothing

        # When: posting credentials without a username
        response = await self.request(
            "post",
            "/pair",
            json={"password": "password"},
        )

        # Then: the request is rejected with a validation error
        self.assertEqual(response.status_code, 400)
