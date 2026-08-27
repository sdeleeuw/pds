from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.mcpserver.exceptions import ToolError
from ninja_jwt.authentication import JWTBaseAuthentication
from ninja_jwt.exceptions import InvalidToken, TokenBackendError, TokenError
from ninja_jwt.settings import api_settings

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

_current_user: ContextVar[AbstractBaseUser | None] = ContextVar(
    "mcp_current_user",
    default=None,
)


class NinjaJWTTokenVerifier(TokenVerifier):
    """Validate MCP Bearer tokens using django-ninja-jwt access tokens."""

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            validated = JWTBaseAuthentication.get_validated_token(token)
        except InvalidToken, TokenError, TokenBackendError:
            return None

        user_id = validated.payload.get(api_settings.USER_ID_CLAIM)

        if user_id is None:
            return None

        return AccessToken(
            token=token,
            client_id=str(user_id),
            scopes=[],
            expires_at=validated.payload.get("exp"),
            subject=str(user_id),
            claims=dict(validated.payload),
        )


async def get_current_user() -> AbstractBaseUser:
    access_token = get_access_token()

    if access_token is not None and access_token.subject:
        User = get_user_model()
        user = await User.objects.filter(
            pk=access_token.subject,
            is_active=True,
        ).afirst()

        if user is not None:
            return user

        raise ToolError("Authentication required")

    user = _current_user.get()

    if user is not None:
        return user

    raise ToolError("Authentication required")


@contextmanager
def as_user(user: AbstractBaseUser) -> Iterator[AbstractBaseUser]:
    token = _current_user.set(user)

    try:
        yield user
    finally:
        _current_user.reset(token)
