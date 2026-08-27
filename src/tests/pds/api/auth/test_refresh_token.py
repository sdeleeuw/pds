from tests.pds.api.auth.base import AuthAPITestCase


class RefreshTokenTests(AuthAPITestCase):
    async def _obtain_refresh_token(self) -> str:
        response = await self.request(
            "post",
            "/pair",
            json={"username": "alice", "password": "password"},
        )

        self.assertEqual(response.status_code, 200)

        return response.json()["refresh"]

    async def test_refresh_token_returns_new_access_token(self):
        # Given: a valid refresh token
        refresh = await self._obtain_refresh_token()

        # When: posting the refresh token
        response = await self.request(
            "post",
            "/refresh",
            json={"refresh": refresh},
        )

        # Then: a new access token is returned
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("access", data)
        self.assertIsInstance(data["access"], str)
        self.assertGreater(len(data["access"]), 0)

    async def test_refresh_token_with_invalid_token(self):
        # Given: a malformed refresh token

        # When: posting the invalid token
        response = await self.request(
            "post",
            "/refresh",
            json={"refresh": "not-a-valid-token"},
        )

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)

    async def test_refresh_token_with_missing_token(self):
        # Given: nothing

        # When: posting an empty body
        response = await self.request("post", "/refresh", json={})

        # Then: the request is rejected with a validation error
        self.assertEqual(response.status_code, 400)
