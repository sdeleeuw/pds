from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
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

_LOCAL_HOSTS = ("127.0.0.1", "localhost", "[::1]")


def _transport_security() -> TransportSecuritySettings:
    # DNS rebinding protection is off under DEBUG so local browsers and MCP
    # clients can reach /mcp without an ALLOWED_HOSTS entry for every port.

    enable_protection = not settings.DEBUG
    hosts: list[str] = []
    origins: list[str] = []

    for host in settings.ALLOWED_HOSTS:
        host = host.strip()

        if not host or host == "*":
            continue

        hosts.append(host)
        hosts.append(f"{host}:*")

        if host in _LOCAL_HOSTS:
            origins.append(f"http://{host}:*")
        else:
            origins.append(f"https://{host}")
            origins.append(f"https://{host}:*")

    if enable_protection and not hosts:
        raise ImproperlyConfigured(
            "MCP DNS rebinding protection is enabled but ALLOWED_HOSTS has no "
            "usable hosts. Set ALLOWED_HOSTS to the public hostname(s) of this "
            "server, or set DEBUG=true to disable protection locally."
        )

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=enable_protection,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def create_mcp_app() -> Starlette:
    return mcp.streamable_http_app(
        streamable_http_path="/",
        transport_security=_transport_security(),
    )
