from __future__ import annotations

from django.conf import settings
from mcp.server import MCPServer
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette

from pds.mcp.auth import NinjaJWTTokenVerifier

mcp = MCPServer(
    "PDS",
    instructions="Personal Data Store MCP server for managing contacts.",
    log_level="WARNING",
    token_verifier=NinjaJWTTokenVerifier(),
    auth=AuthSettings(
        issuer_url=settings.MCP_ISSUER_URL,
        resource_server_url=None,
        required_scopes=None,
    ),
)


def _transport_security() -> TransportSecuritySettings:
    hosts: list[str] = []
    origins: list[str] = []

    for host in settings.ALLOWED_HOSTS:
        host = host.strip()

        if not host or host == "*":
            continue

        hosts.append(host)
        hosts.append(f"{host}:*")

        if host in ("127.0.0.1", "localhost", "[::1]"):
            origins.append(f"http://{host}:*")
        else:
            origins.append(f"https://{host}")
            origins.append(f"https://{host}:*")
            origins.append(f"http://{host}")
            origins.append(f"http://{host}:*")

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=not settings.DEBUG,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def create_mcp_app() -> Starlette:
    return mcp.streamable_http_app(
        streamable_http_path="/",
        transport_security=_transport_security(),
    )
