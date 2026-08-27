from __future__ import annotations

from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.mcpserver.exceptions import ToolError
from ninja_jwt.exceptions import TokenBackendError, TokenError
from ninja_jwt.settings import api_settings

from pds.mcp.tokens import MCPToken

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser


class NinjaJWTTokenVerifier(TokenVerifier):
    """Validate MCP Bearer tokens as dedicated django-ninja-jwt MCP tokens."""

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            validated = await sync_to_async(MCPToken)(token)
        except TokenError, TokenBackendError:
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

    if access_token is None or not access_token.subject:
        raise ToolError("Authentication required")

    User = get_user_model()
    user = await User.objects.filter(
        pk=access_token.subject,
        is_active=True,
    ).afirst()

    if user is None:
        raise ToolError("Authentication required")

    return user
