# Personal Data Store

A Django 6.1 app that stores contacts for authenticated users and exposes them
through two entry points that share one set of models and schemas:

- a REST API (django-ninja-extra + JWT)
- an MCP server (Streamable HTTP) for AI clients

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)

## Quick start

```bash
uv sync --frozen
cp .env.example .env
cd src
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

`SECRET_KEY` has no default; copy `.env.example` or Django will refuse to start.

`manage.py runserver` serves Django only (admin and REST). The MCP endpoint is
mounted in ASGI, so serve `pds.asgi:application` to get both:

```bash
cd src
uv run uvicorn pds.asgi:application --reload
```

Then:

| URL | What |
| --- | --- |
| http://localhost:8000/admin/ | Django admin |
| http://localhost:8000/api/docs | OpenAPI UI |
| http://localhost:8000/mcp | MCP Streamable HTTP |

## REST API

All contact routes require a Bearer access token. Tokens last 15 minutes;
refresh tokens last 14 days.

### Auth

```http
POST /api/auth/pair
Content-Type: application/json

{"username": "alice", "password": "password123"}
```

Returns `access`, `refresh`, and `username`.

```http
POST /api/auth/refresh
Content-Type: application/json

{"refresh": "<refresh_token>"}
```

```http
POST /api/auth/verify
Content-Type: application/json

{"token": "<access_token>"}
```

### Contacts

Authorization is per owner: a missing contact and someone else's contact both
look like 404.

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/contacts/` | List the signed-in user's contacts |
| `GET` | `/api/contacts/{id}/` | Retrieve one contact |
| `POST` | `/api/contacts/` | Create (201) |
| `PATCH` | `/api/contacts/{id}/` | Partial update |
| `DELETE` | `/api/contacts/{id}/` | Delete (204) |

Contact fields: `first_name`, `last_name`, `email`, `mobile_phone`,
`home_phone`, `address`, `postal_code`, `city`, `region`, `country`,
`date_of_birth`, `notes`. Responses also include computed `name` and `age`,
plus `id`, `created_at`, and `updated_at`.

Email is unique per owner when it is non-blank; blank emails are allowed and
non-unique.

## MCP

The server at `/mcp` is Streamable HTTP. A trailing slash is optional.

Tools (scoped to the authenticated user):

| Tool | What |
| --- | --- |
| `search_contacts` | Case-insensitive substring search (name, email, phones, address, notes). Empty query is rejected. Default limit 50, max 100. |
| `list_contacts` | List contacts (same limit) |
| `get_contact` | Retrieve one contact by id |
| `create_contact` | Create a contact |
| `update_contact` | Partial update (omitted fields are left unchanged) |
| `delete_contact` | Permanently delete a contact |

### Authentication

`/mcp` requires a dedicated MCP token. REST access tokens from `/api/auth/pair`
are not accepted, and MCP tokens are not accepted by the REST API.

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

3. Send the MCP token as a Bearer header against `/mcp`:

    ```http
    Authorization: Bearer <mcp_token>
    ```

MCP tokens last 90 days by default (`MCP_TOKEN_LIFETIME_DAYS`). Revoke every
outstanding MCP token for the signed-in user with:

```http
DELETE /api/auth/mcp-token
Authorization: Bearer <access_token>
```

Example MCP client config:

```json
{
  "mcpServers": {
    "pds": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer <mcp_token>"
      }
    }
  }
}
```

## Configuration

Settings are read through `python-decouple` `config()` from the environment or
`.env`:

| Variable | Default | Notes |
| --- | --- | --- |
| `SECRET_KEY` | *(required)* | Django secret |
| `DEBUG` | `false` | `true` in `.env.example`. Disables MCP DNS rebinding protection. |
| `ALLOWED_HOSTS` | empty | Comma-separated. Required in production (`DEBUG=false`) so MCP can allow the public hostname. |
| `DATABASE_URL` | SQLite at `src/db.sqlite3` | Any URL `dj-database-url` accepts |
| `MCP_ISSUER_URL` | `http://localhost:8000/api/auth` | Advertised issuer; authorization-server routes are not mounted |
| `MCP_TOKEN_LIFETIME_DAYS` | `90` | MCP token lifetime |

## Development

```bash
uv run ruff check .
uv run ruff format .

cd src && DJANGO_SETTINGS_MODULE=pds.settings_test uv run python manage.py test
```

CI sets `DJANGO_SETTINGS_MODULE=pds.settings_test`. The default `pds.settings`
will not have `testserver` in `ALLOWED_HOSTS`.

Layout (Python packages live under `src/`):

- `src/pds/` — project config, ASGI mount, MCP server and token type
- `src/contacts/` — models, schemas, REST API, MCP tools, admin
- `src/tests/` — tests mirroring those apps; shared fixtures in `tests/fixtures/`

Contributor conventions (async ORM, queryset-based auth, test layout) live in
[`AGENTS.md`](AGENTS.md).
