# Personal Data Store

## MCP authentication

The MCP server at `/mcp` requires a django-ninja-jwt access token.

1. Obtain tokens from the API:

```http
POST /api/auth/pair
Content-Type: application/json

{"username": "alice", "password": "password123"}
```

2. Configure your MCP client to send the access token as a Bearer header against
   the Streamable HTTP endpoint:

```http
Authorization: Bearer <access_token>
```

Access tokens expire after 15 minutes (`NINJA_JWT.ACCESS_TOKEN_LIFETIME`). Use the
refresh token from `/api/auth/pair` (or `/api/auth/refresh`) to obtain a new access
token when needed.
