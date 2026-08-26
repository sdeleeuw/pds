from pds.tests.api.auth.base import AuthAPITestCase


class VerifyTokenTests(AuthAPITestCase):
    async def _obtain_access_token(self) -> str:
        response = await self.request(
            "post",
            "/pair",
            json={"username": "alice", "password": "password123"},
        )

        self.assertEqual(response.status_code, 200)

        return response.json()["access"]

    async def _obtain_refresh_token(self) -> str:
        response = await self.request(
            "post",
            "/pair",
            json={"username": "alice", "password": "password123"},
        )

        self.assertEqual(response.status_code, 200)

        return response.json()["refresh"]

    async def test_verify_with_valid_access_token(self):
        # Given: a valid access token
        access = await self._obtain_access_token()

        # When: verifying the token
        response = await self.request(
            "post",
            "/verify",
            json={"token": access},
        )

        # Then: the token is accepted
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    async def test_verify_with_valid_refresh_token(self):
        # Given: a valid refresh token
        refresh = await self._obtain_refresh_token()

        # When: verifying the refresh token
        response = await self.request(
            "post",
            "/verify",
            json={"token": refresh},
        )

        # Then: the token is accepted
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    async def test_verify_with_invalid_token(self):
        # Given: a malformed token

        # When: posting an invalid token
        response = await self.request(
            "post",
            "/verify",
            json={"token": "not-a-valid-token"},
        )

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)

    async def test_verify_with_missing_token(self):
        # Given: nothing

        # When: posting an empty body
        response = await self.request("post", "/verify", json={})

        # Then: the request is rejected with a validation error
        self.assertEqual(response.status_code, 400)
