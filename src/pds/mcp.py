from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

_current_user: ContextVar[AbstractBaseUser | None] = ContextVar(
    "mcp_current_user",
    default=None,
)


async def get_current_user() -> AbstractBaseUser:
    user = _current_user.get()

    if user is not None:
        return user

    username = getattr(settings, "MCP_USERNAME", "") or ""

    if username:
        User = get_user_model()
        try:
            return await User.objects.aget(username=username)
        except User.DoesNotExist as exc:
            raise ToolError(f"Configured MCP user {username!r} not found") from exc

    raise ToolError("Authentication required")


@contextmanager
def as_user(user: AbstractBaseUser) -> Iterator[AbstractBaseUser]:
    token = _current_user.set(user)

    try:
        yield user
    finally:
        _current_user.reset(token)


mcp = MCPServer(
    "PDS",
    instructions="Personal Data Store MCP server for managing contacts.",
    log_level="WARNING",
)
