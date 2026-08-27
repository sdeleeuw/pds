from datetime import timedelta

from asgiref.sync import sync_to_async
from django.test import TestCase
from ninja_jwt.tokens import AccessToken, RefreshToken
from ninja_jwt.utils import aware_utcnow

from pds.mcp.auth import NinjaJWTTokenVerifier
from pds.mcp.tokens import MCPToken
from pds.tests.fixtures import create_user


class TokenVerifierTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(username="alice", email="alice@example.com")
        cls.verifier = NinjaJWTTokenVerifier()

    async def test_valid_mcp_token(self):
        # Given: a valid MCP token for an existing user
        mcp_token = await sync_to_async(MCPToken.for_user)(self.user)
        raw = str(mcp_token)

        # When: verifying the token
        result = await self.verifier.verify_token(raw)

        # Then: an AccessToken is returned with the user as subject
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.subject, str(self.user.pk))
        self.assertEqual(result.client_id, str(self.user.pk))
        self.assertEqual(result.token, raw)
        self.assertEqual(result.expires_at, mcp_token.payload["exp"])
        self.assertEqual(result.claims["user_id"], self.user.pk)

    async def test_rest_access_token_rejected(self):
        # Given: a REST API access token
        raw = str(AccessToken.for_user(self.user))

        # When: verifying the token
        result = await self.verifier.verify_token(raw)

        # Then: verification fails because the token type is not mcp
        self.assertIsNone(result)

    async def test_refresh_token_rejected(self):
        # Given: a refresh token (not an MCP token)
        refresh = str(await sync_to_async(RefreshToken.for_user)(self.user))

        # When: verifying the refresh token
        result = await self.verifier.verify_token(refresh)

        # Then: verification fails
        self.assertIsNone(result)

    async def test_garbage_token_rejected(self):
        # Given: a non-JWT string

        # When: verifying garbage
        result = await self.verifier.verify_token("not-a-jwt")

        # Then: verification fails without raising
        self.assertIsNone(result)

    async def test_wrong_signature_rejected(self):
        # Given: a token with a tampered signature
        raw = str(await sync_to_async(MCPToken.for_user)(self.user))
        parts = raw.split(".")
        tampered = f"{parts[0]}.{parts[1]}.{parts[2][:-4]}xxxx"

        # When: verifying the tampered token
        result = await self.verifier.verify_token(tampered)

        # Then: verification fails
        self.assertIsNone(result)

    async def test_expired_token_rejected(self):
        # Given: an MCP token whose exp claim is in the past
        mcp_token = await sync_to_async(MCPToken.for_user)(self.user)
        mcp_token.set_exp(
            from_time=aware_utcnow() - timedelta(hours=1),
            lifetime=timedelta(seconds=1),
        )
        raw = str(mcp_token)

        # When: verifying the expired token
        result = await self.verifier.verify_token(raw)

        # Then: verification fails
        self.assertIsNone(result)

    async def test_blacklisted_token_rejected(self):
        # Given: an MCP token that has been revoked
        mcp_token = await sync_to_async(MCPToken.for_user)(self.user)
        raw = str(mcp_token)
        await sync_to_async(mcp_token.blacklist)()

        # When: verifying the blacklisted token
        result = await self.verifier.verify_token(raw)

        # Then: verification fails
        self.assertIsNone(result)
