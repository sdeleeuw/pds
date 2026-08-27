"""
ASGI config for pds project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount
from starlette.types import ASGIApp, Receive, Scope, Send

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pds.settings")

# Django must be configured before importing pds.mcp.server: ninja_jwt reads
# settings.SECRET_KEY at import time via api_settings.
django_app = get_asgi_application()

from pds.mcp.server import create_mcp_app, mcp  # noqa: E402


class _NormalizeMCPPath:
    """Serve /mcp as /mcp/ so clients need not use a trailing slash.

    ``Mount("/mcp")`` only matches ``/mcp/...``. Without this rewrite a request
    to ``/mcp`` falls through to Django and 404s.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"] == "/mcp":
            scope = dict(scope)
            scope["path"] = "/mcp/"
            scope["raw_path"] = b"/mcp/"
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with mcp.session_manager.run():
        yield


def create_application() -> Starlette:
    return Starlette(
        routes=[
            Mount("/mcp", app=create_mcp_app()),
            Mount("/", app=django_app),
        ],
        middleware=[Middleware(_NormalizeMCPPath)],
        lifespan=lifespan,
    )


application = create_application()
