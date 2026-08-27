from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import anyio
from django.test import TestCase
from mcp.shared.inbound import (
    MCP_METHOD_HEADER,
    MCP_NAME_HEADER,
    MCP_PROTOCOL_VERSION_HEADER,
)
from mcp_types import CLIENT_CAPABILITIES_META_KEY, PROTOCOL_VERSION_META_KEY
from mcp_types.version import LATEST_MODERN_VERSION
from ninja_jwt.tokens import AccessToken, RefreshToken
from ninja_jwt.utils import aware_utcnow

from contacts.tests.fixtures import create_contact, create_user
from pds.mcp import create_mcp_app, mcp


@dataclass
class ASGIResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes

    def json(self) -> Any:
        return json.loads(self.body)


async def asgi_request(
    app,
    *,
    method: str = "POST",
    path: str = "/",
    headers: Mapping[str, str] | None = None,
    body: bytes | dict | None = None,
) -> ASGIResponse:
    if isinstance(body, dict):
        body_bytes = json.dumps(body).encode()
    elif body is None:
        body_bytes = b""
    else:
        body_bytes = body

    header_list = [
        (b"host", b"testserver"),
        (b"content-type", b"application/json"),
        (b"accept", b"application/json, text/event-stream"),
        (b"content-length", str(len(body_bytes)).encode()),
    ]

    for key, value in (headers or {}).items():
        header_list.append((key.lower().encode(), value.encode()))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": header_list,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }

    body_sent = False
    response_status = 500
    response_headers: dict[str, str] = {}
    response_body = bytearray()

    async def receive():
        nonlocal body_sent

        if not body_sent:
            body_sent = True
            return {
                "type": "http.request",
                "body": body_bytes,
                "more_body": False,
            }

        await anyio.sleep_forever()
        return {"type": "http.disconnect"}

    async def send(message):
        nonlocal response_status, response_headers, response_body

        if message["type"] == "http.response.start":
            response_status = message["status"]
            response_headers = {
                key.decode().lower(): value.decode()
                for key, value in message.get("headers", [])
            }
        elif message["type"] == "http.response.body":
            response_body.extend(message.get("body", b""))

    await app(scope, receive, send)

    return ASGIResponse(
        status_code=response_status,
        headers=response_headers,
        body=bytes(response_body),
    )


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

    def access_token(self, user=None) -> str:
        return str(RefreshToken.for_user(user or self.user).access_token)

    def expired_access_token(self, user=None) -> str:
        access = AccessToken.for_user(user or self.user)
        access.set_exp(
            from_time=aware_utcnow() - timedelta(hours=1),
            lifetime=timedelta(seconds=1),
        )
        return str(access)

    def tools_call_body(self, name: str, arguments: dict | None = None) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments or {},
                "_meta": {
                    PROTOCOL_VERSION_META_KEY: LATEST_MODERN_VERSION,
                    CLIENT_CAPABILITIES_META_KEY: {},
                },
            },
        }

    def tools_call_headers(
        self, name: str, *, authorization: str | None
    ) -> dict[str, str]:
        headers = {
            MCP_PROTOCOL_VERSION_HEADER: LATEST_MODERN_VERSION,
            MCP_METHOD_HEADER: "tools/call",
            MCP_NAME_HEADER: name,
        }

        if authorization is not None:
            headers["Authorization"] = authorization

        return headers

    async def post_mcp(
        self,
        *,
        authorization: str | None = None,
        body: dict | bytes | None = None,
        tool_name: str | None = None,
    ) -> ASGIResponse:
        app = create_mcp_app()

        if tool_name is not None and body is None:
            body = self.tools_call_body(tool_name)
            headers = self.tools_call_headers(tool_name, authorization=authorization)
        else:
            headers = {}
            if authorization is not None:
                headers["Authorization"] = authorization
            if tool_name is not None:
                headers.update(
                    self.tools_call_headers(tool_name, authorization=authorization)
                )

        async with mcp.session_manager.run():
            return await asgi_request(
                app,
                headers=headers,
                body=body if body is not None else b"",
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

    async def test_expired_token_returns_401(self):
        # Given: an expired access token

        # When: posting with that token
        response = await self.post_mcp(
            authorization=f"Bearer {self.expired_access_token()}",
        )

        # Then: the request is rejected
        self.assertEqual(response.status_code, 401)
        self.assertIn("bearer", response.headers.get("www-authenticate", "").lower())

    async def test_valid_token_lists_own_contacts(self):
        # Given: a valid access token for a user with an owned contact

        # When: calling list_contacts over Streamable HTTP
        response = await self.post_mcp(
            authorization=f"Bearer {self.access_token()}",
            tool_name="list_contacts",
        )

        # Then: the call succeeds and only the token user's contacts are returned
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertNotIn("error", payload)
        result = payload["result"]
        self.assertFalse(result.get("isError", False))

        structured = result.get("structuredContent")
        if (
            isinstance(structured, dict)
            and "result" in structured
            and len(structured) == 1
        ):
            contacts = structured["result"]
        else:
            contacts = structured

        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]["id"], self.contact.id)
        self.assertEqual(contacts[0]["email"], "jane@example.com")
