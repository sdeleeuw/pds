from asgiref.sync import sync_to_async
from ninja_jwt.tokens import AccessToken

from pds.mcp.auth import NinjaJWTTokenVerifier
from pds.mcp.tokens import MCPToken
from tests.pds.api.auth.base import AuthAPITestCase


class MCPTokenAPITests(AuthAPITestCase):
    def access_header(self, user=None) -> dict[str, str]:
        token = str(AccessToken.for_user(user or self.user))
        return {"Authorization": f"Bearer {token}"}

    async def test_create_mcp_token(self):
        # Given: an authenticated REST user

        # When: minting an MCP token
        response = await self.request(
            "post",
            "/mcp-token",
            headers=self.access_header(),
        )

        # Then: a dedicated MCP token is returned
        self.assertEqual(response.status_code, 200)
        token = response.json()["token"]
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
        decoded = await sync_to_async(MCPToken)(token)
        self.assertEqual(decoded["user_id"], self.user.pk)

    async def test_create_mcp_token_unauthenticated(self):
        # Given: no REST credentials

        # When: minting an MCP token
        response = await self.request("post", "/mcp-token")

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)

    async def test_mcp_token_rejected_by_rest_api(self):
        # Given: an MCP token
        mcp_token = str(await sync_to_async(MCPToken.for_user)(self.user))

        # When: calling a REST endpoint with it
        response = await self.client.get(
            "/contacts/",
            headers={"Authorization": f"Bearer {mcp_token}"},
        )

        # Then: the REST API rejects the token type
        self.assertEqual(response.status_code, 401)

    async def test_revoke_mcp_token(self):
        # Given: an outstanding MCP token
        mcp_token = str(await sync_to_async(MCPToken.for_user)(self.user))
        verifier = NinjaJWTTokenVerifier()
        self.assertIsNotNone(await verifier.verify_token(mcp_token))

        # When: revoking MCP tokens for the user
        response = await self.request(
            "delete",
            "/mcp-token",
            headers=self.access_header(),
        )

        # Then: the token is no longer valid
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(await verifier.verify_token(mcp_token))

    async def test_revoke_mcp_token_unauthenticated(self):
        # Given: no REST credentials

        # When: revoking MCP tokens
        response = await self.request("delete", "/mcp-token")

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)
