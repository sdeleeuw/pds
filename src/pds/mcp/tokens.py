from django.conf import settings
from django.contrib.auth import get_user_model
from ninja_jwt.exceptions import TokenError
from ninja_jwt.token_blacklist.models import OutstandingToken
from ninja_jwt.tokens import BlacklistMixin, Token

User = get_user_model()


class MCPToken(BlacklistMixin, Token):
    """Long-lived token accepted only by the MCP server, not the REST API."""

    token_type = "mcp"
    lifetime = settings.MCP_TOKEN_LIFETIME


def issue_mcp_token(user: User) -> MCPToken:
    return MCPToken.for_user(user)


def revoke_mcp_tokens_for_user(user: User) -> int:
    revoked = 0

    for outstanding in OutstandingToken.objects.filter(user=user):
        try:
            token = MCPToken(outstanding.token)
        except TokenError:
            continue

        token.blacklist()
        revoked += 1

    return revoked
