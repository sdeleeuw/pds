from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
from starlette.types import ASGIApp


@asynccontextmanager
async def run_lifespan(app: ASGIApp) -> AsyncIterator[None]:
    """Drive ASGI lifespan so the MCP session manager is started."""
    startup_complete = anyio.Event()
    shutdown = anyio.Event()
    startup_error: str | None = None
    startup_sent = False

    async def receive():
        nonlocal startup_sent

        if not startup_sent:
            startup_sent = True
            return {"type": "lifespan.startup"}

        await shutdown.wait()
        return {"type": "lifespan.shutdown"}

    async def send(message):
        nonlocal startup_error
        message_type = message["type"]

        if message_type == "lifespan.startup.complete":
            startup_complete.set()
        elif message_type == "lifespan.startup.failed":
            startup_error = message.get("message", "lifespan startup failed")
            startup_complete.set()

    async with anyio.create_task_group() as tg:
        tg.start_soon(
            app,
            {"type": "lifespan", "asgi": {"version": "3.0"}},
            receive,
            send,
        )
        await startup_complete.wait()

        if startup_error is not None:
            raise RuntimeError(startup_error)

        try:
            yield
        finally:
            shutdown.set()
