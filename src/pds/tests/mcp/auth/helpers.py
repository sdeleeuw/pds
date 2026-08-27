from collections.abc import Iterator
from contextlib import contextmanager

from django.contrib.auth.models import AbstractBaseUser
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken


@contextmanager
def mcp_access_token(
    *,
    subject: str | None,
    client_id: str | None = None,
    token: str = "test-token",
) -> Iterator[None]:
    access = AccessToken(
        token=token,
        client_id=client_id if client_id is not None else (subject or "unknown"),
        scopes=[],
        subject=subject,
    )
    ctx = auth_context_var.set(AuthenticatedUser(access))

    try:
        yield
    finally:
        auth_context_var.reset(ctx)


@contextmanager
def authenticated_as(user: AbstractBaseUser) -> Iterator[None]:
    with mcp_access_token(subject=str(user.pk)):
        yield
