from django.test import TestCase

from pds.asgi import create_application
from pds.mcp.server import mcp
from pds.tests.mcp.http.helpers import run_lifespan

from .test_auth import MCPHTTPAuthTestCase


class MCPASGIMountTests(MCPHTTPAuthTestCase):
    async def test_mcp_without_trailing_slash_reaches_mcp_server(self):
        # Given: the combined Django + MCP ASGI application

        # When: posting to /mcp without a trailing slash and no token
        response = await self.post_mcp(path="/mcp")

        # Then: the MCP auth middleware answers, not Django
        self.assertEqual(response.status_code, 401)
        self.assertIn("bearer", response.headers.get("www-authenticate", "").lower())

    async def test_mcp_with_trailing_slash_reaches_mcp_server(self):
        # Given: the combined Django + MCP ASGI application

        # When: posting to /mcp/ with no token
        response = await self.post_mcp(path="/mcp/")

        # Then: the MCP auth middleware answers, not Django
        self.assertEqual(response.status_code, 401)
        self.assertIn("bearer", response.headers.get("www-authenticate", "").lower())

    async def test_django_passthrough(self):
        # Given: the combined Django + MCP ASGI application

        # When: requesting a Django route
        async with self.asgi_client() as client:
            response = await client.get("/admin/login/")

        # Then: Django handles the request
        self.assertEqual(response.status_code, 200)

    async def test_lifespan_starts_session_manager_once(self):
        # Given: a freshly built ASGI application
        app = create_application()

        # When: the application lifespan runs
        async with run_lifespan(app):
            # Then: the MCP session manager has started and cannot be started again
            self.assertTrue(mcp.session_manager._has_started)

            with self.assertRaises(RuntimeError):
                async with mcp.session_manager.run():
                    pass


class MCPTransportSecurityTests(TestCase):
    def test_empty_allowed_hosts_raises_when_protection_enabled(self):
        from django.core.exceptions import ImproperlyConfigured
        from django.test import override_settings

        from pds.mcp.server import _transport_security

        # Given: production settings with no usable hosts
        with override_settings(DEBUG=False, ALLOWED_HOSTS=["", "*"]):
            # When/Then: transport security refuses to start with an empty allowlist
            with self.assertRaises(ImproperlyConfigured):
                _transport_security()

    def test_non_local_hosts_do_not_allow_http_origins(self):
        from django.test import override_settings

        from pds.mcp.server import _transport_security

        # Given: a public hostname
        with override_settings(DEBUG=False, ALLOWED_HOSTS=["pds.example"]):
            # When: building transport security
            security = _transport_security()

        # Then: only https origins are allowed
        self.assertTrue(security.enable_dns_rebinding_protection)
        self.assertIn("https://pds.example", security.allowed_origins)
        self.assertIn("https://pds.example:*", security.allowed_origins)
        self.assertNotIn("http://pds.example", security.allowed_origins)
        self.assertNotIn("http://pds.example:*", security.allowed_origins)
