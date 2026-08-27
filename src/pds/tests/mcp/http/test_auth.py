from __future__ import annotations

from contextlib import asynccontextmanager

import httpx2
from asgiref.sync import sync_to_async
from django.test import TestCase
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from ninja_jwt.tokens import AccessToken

from contacts.tests.fixtures import create_contact, create_user
from pds.asgi import create_application
from pds.mcp.tokens import MCPToken
from pds.tests.mcp.http.helpers import run_lifespan


class MCPHTTPAuthTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(username="alice", email="alice@example.com")
        cls.other_user = create_user(username="bob", email="bob@example.com")
        cls.contact = create_contact(
            owner=cls.user,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
        )
        cls.other_contact = create_contact(
            owner=cls.other_user,
            first_name="John",
            last_name="Smith",
            email="john@example.com",
        )

    async def mcp_token(self, user=None) -> str:
        return str(await sync_to_async(MCPToken.for_user)(user or self.user))

    @asynccontextmanager
    async def asgi_client(self, *, authorization: str | None = None):
        app = create_application()
        headers = {}

        if authorization is not None:
            headers["Authorization"] = authorization

        async with run_lifespan(app):
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://testserver",
                headers=headers,
            ) as client:
                yield client

    async def post_mcp(
        self,
        *,
        path: str = "/mcp",
        authorization: str | None = None,
    ) -> httpx2.Response:
        async with self.asgi_client(authorization=authorization) as client:
            return await client.post(
                path,
                headers={"accept": "application/json, text/event-stream"},
                content=b"{}",
            )


class MCPHTTPAuthTests(MCPHTTPAuthTestCase):
    async def test_missing_authorization_returns_401(self):
        # Given: no Authorization header

        # When: posting to the MCP endpoint
        response = await self.post_mcp()

        # Then: the request is rejected with a Bearer challenge
        self.assertEqual(response.status_code, 401)
        self.assertIn("bearer", response.headers.get("www-authenticate", "").lower())

    async def test_invalid_token_returns_401(self):
        # Given: a malformed bearer token

        # When: posting with that token
        response = await self.post_mcp(authorization="Bearer not-a-jwt")

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)
        self.assertIn("bearer", response.headers.get("www-authenticate", "").lower())

    async def test_rest_access_token_returns_401(self):
        # Given: a REST API access token rather than an MCP token

        # When: posting with that token
        response = await self.post_mcp(
            authorization=f"Bearer {AccessToken.for_user(self.user)}",
        )

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)

    async def test_valid_token_lists_own_contacts(self):
        # Given: a valid MCP token for a user with an owned contact

        # When: calling list_contacts over Streamable HTTP
        async with self.asgi_client(
            authorization=f"Bearer {await self.mcp_token()}",
        ) as http:
            async with Client(
                streamable_http_client("http://testserver/mcp", http_client=http)
            ) as client:
                result = await client.call_tool("list_contacts")

        # Then: the call succeeds and only the token user's contacts are returned
        self.assertFalse(result.is_error)
        contacts = result.structured_content
        if isinstance(contacts, dict) and "result" in contacts and len(contacts) == 1:
            contacts = contacts["result"]

        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]["id"], self.contact.id)
        self.assertEqual(contacts[0]["email"], "jane@example.com")
