# Personal Data Store

## MCP authentication

The MCP server at `/mcp` requires a dedicated MCP token. REST access tokens from
`/api/auth/pair` are not accepted.

1. Obtain a REST access token:

```http
POST /api/auth/pair
Content-Type: application/json

{"username": "alice", "password": "password123"}
```

2. Mint an MCP token (requires the access token from step 1):

```http
POST /api/auth/mcp-token
Authorization: Bearer <access_token>
```

3. Configure your MCP client to send the MCP token as a Bearer header against
   the Streamable HTTP endpoint at `/mcp` (a trailing slash is optional):

```http
Authorization: Bearer <mcp_token>
```

MCP tokens last 90 days by default (`MCP_TOKEN_LIFETIME_DAYS`). Revoke every
outstanding MCP token for the signed-in user with:

```http
DELETE /api/auth/mcp-token
Authorization: Bearer <access_token>
```
