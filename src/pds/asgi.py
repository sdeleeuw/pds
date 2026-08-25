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
from starlette.routing import Mount

from pds.mcp import mcp

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pds.settings")

django_app = get_asgi_application()
mcp_app = mcp.streamable_http_app(streamable_http_path="/")


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with mcp.session_manager.run():
        yield


application = Starlette(
    routes=[
        Mount("/mcp", app=mcp_app),
        Mount("/", app=django_app),
    ],
    lifespan=lifespan,
)
