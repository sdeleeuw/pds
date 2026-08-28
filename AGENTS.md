# AGENTS.md

Personal Data Store: a Django 6.1 project exposing contacts over both a REST API
(django-ninja-extra) and an MCP server (Streamable HTTP), sharing one set of
models and schemas.

## Layout

Python packages live under `src/`, which is the working directory for every
Django command. `manage.py` is at `src/manage.py`, not the repo root.

- `src/pds/` — project config: `settings.py`, `settings_test.py`, `urls.py`,
  `asgi.py`, plus `pds/mcp/` (MCP server, token type, token verifier) and
  `pds/mixins/`.
- `src/contacts/` — the one feature app, split into per-concern packages:
  `models/`, `schemas/`, `api/`, `mcp/`, `admin/`.
- `src/tests/` — all tests in one package. Domain trees mirror the apps
  (`tests/contacts/api/contact/`, `tests/contacts/mcp/contact/`,
  `tests/pds/api/auth/`, `tests/pds/mcp/`). Shared fixtures live in
  `tests/fixtures/`.

Every package directory re-exports its public names from `__init__.py` with an
explicit `__all__`. When you add a module to `models/`, `schemas/`, `api/`,
`mcp/`, or `admin/`, add it to that package's `__init__.py` too.

## Commands

Dependencies are managed with `uv` (Python 3.14, `uv.lock` is committed). Use
`uv run`; do not activate the venv manually or call `pip`.

```bash
uv sync --frozen                    # install exactly what CI installs

uv run ruff check .                 # lint (E, F; E501 ignored; migrations excluded)
uv run ruff format .                # format — CI runs `ruff format --check .`

cd src && uv run python manage.py test                                    # full suite
cd src && uv run python manage.py test tests.contacts.mcp.contact         # one package
cd src && uv run python manage.py test tests.contacts.mcp.contact.test_update.UpdateContactTests.test_update_contact
```

Tests require `DJANGO_SETTINGS_MODULE=pds.settings_test`. CI sets it as a job
env var, so it is easy to forget locally — the default `pds.settings` will
produce log noise and will not have `testserver` in `ALLOWED_HOSTS`. `SECRET_KEY`
has no default and must be set (via `.env` or the environment) or Django refuses
to start.

Settings are read through `python-decouple` `config()`: `SECRET_KEY` (required),
`DEBUG`, `ALLOWED_HOSTS` (comma-separated), `DATABASE_URL` (defaults to SQLite at
`src/db.sqlite3`), `MCP_ISSUER_URL`, `MCP_TOKEN_LIFETIME_DAYS`.

## Conventions

**Everything is async.** API views, MCP tools, and test methods are `async def`,
and they use the async ORM: `acreate`, `asave`, `adelete`, `afirst`,
`aget_object_or_404`, `arefresh_from_db`, and `async for` over querysets. Sync-only
code (django-ninja-jwt token construction, `Token.for_user`) must be wrapped in
`sync_to_async`.

**Authorization goes through the queryset.** `ContactQuerySet` exposes
`readable_for_user(user)` and `writable_for_user(user)`; both API and MCP layers
define a local `get_queryset(...)` / `get_object(...)` pair that picks one based
on whether the operation writes. Never filter by `owner` inline in a view or
tool — a missing object and a forbidden object should be indistinguishable
(404 / "not found"), which is what the tests assert.

**Two entry points, one schema.** `contacts/schemas/contact.py` holds
`ContactSchema` (output, a `ModelSchema` including the `name` and `age`
properties) and `ContactCreateUpdateSchema` (input). The REST layer wraps the
input schema in `PatchDict[...]` for PATCH; the MCP layer takes it directly and
uses `payload.dict(exclude_unset=True)`. Add new fields to the model, the
migration, both schemas, and the admin `search_fields`/`list_display`.

**MCP tools** are registered with `@mcp.tool()` in `contacts/mcp/contact.py`.
Each tool annotates its arguments with `Annotated[..., Field(description=...)]`,
takes the current user as a keyword-only
`user: Annotated[User, Resolve(get_current_user)]`, and raises
`ToolError("...")` with a user-facing message for every failure (not found,
validation, `IntegrityError`). Tool registration happens as an import side
effect in `ContactsConfig.ready()` — a new MCP module must be imported there or
its tools will silently not exist.

**User-facing descriptions omit ownership.** REST view docstrings become the
OpenAPI `description`; MCP tool docstrings become the tool description. Write
the operation (`Create a contact`, `Get a single contact`), not who it is
scoped to. Do not say "authenticated user", "current user", or "owned by the
user" — queryset filtering already makes that true, and clients already know
they are acting as themselves. Note when relevant that returned `name` and
`age` are computed and read-only; field-level details belong in schema
`Field(description=...)` text, not the operation docstring.

**Tests** use `django.test.TestCase` with class data built in `setUpTestData`,
and shared fixtures `create_user` / `create_contact` from `tests.fixtures`
rather than inline object creation. Each test package has a `base.py` with a
`...TestCase` holding fixtures and a request/call helper; test modules are named
after the operation (`test_create.py`, `test_update.py`) and contain only test
classes. Test bodies follow a literal `# Given:` / `# When:` / `# Then:` comment
structure — match it.

Commit messages are Conventional Commits: `feat:`, `fix:`, `test:`.

## Gotchas

**`/mcp` is mounted in ASGI, not in `urls.py`.** `pds/asgi.py` builds a Starlette
app that mounts the MCP app at `/mcp` and the Django app at `/`. Consequences:

- `get_asgi_application()` must be called *before* importing `pds.mcp.server`,
  because `ninja_jwt` reads `settings.SECRET_KEY` at import time. The
  `# noqa: E402` on that import is deliberate.
- `Mount("/mcp")` only matches `/mcp/...`, so `_NormalizeMCPPath` middleware
  rewrites bare `/mcp` to `/mcp/`. Without it the request falls through to
  Django and 404s.
- The MCP session manager is started by the Starlette lifespan. Tests that hit
  the endpoint over HTTP must drive lifespan via
  `tests.pds.mcp.http.helpers.run_lifespan`; the session manager can only be
  started once per app.
- Running `manage.py runserver` gets you Django only, without `/mcp`. Serve
  `pds.asgi:application` through an ASGI server to exercise the MCP endpoint.

**MCP tokens are a separate token type.** `MCPToken` (`token_type = "mcp"`,
90-day lifetime) is minted at `POST /api/auth/mcp-token` using a REST access
token, and revoked via `DELETE /api/auth/mcp-token`. A normal `AccessToken` sent
to `/mcp` must be rejected with 401, and vice versa — there are tests for both
directions. Do not relax `NinjaJWTTokenVerifier` to accept generic tokens.

**DNS rebinding protection is tied to `DEBUG`.** `_transport_security()` disables
it when `DEBUG` is true, and raises `ImproperlyConfigured` when `DEBUG` is false
and `ALLOWED_HOSTS` has no usable host. Non-local hosts get `https://` origins
only.

**Testing MCP tools two ways.** In-process tool tests use `mcp.Client(mcp)` plus
the `authenticated_as(user)` context manager, which sets the MCP auth context var
directly. HTTP-level tests use `httpx2.ASGITransport` against
`create_application()` with a real `Authorization` header. Prefer the in-process
form for tool behaviour and reserve the HTTP form for auth and mounting.

**Structured tool output may be wrapped.** Tools returning a list come back as
`{"result": [...]}` in `result.structured_content`. `base.py` has a
`contact_data(result)` helper that unwraps it; use it instead of indexing
`structured_content` directly.

**Contact uniqueness.** A partial unique constraint on `(owner, email)` applies
only when `email != ""` (blank emails are allowed and non-unique). Writes must
catch `IntegrityError` and surface an actionable message.

**`Contact.owner` is `on_delete=PROTECT`**, so users with contacts cannot be
deleted until their contacts are gone.

**Python 3.14 syntax is in use.** `pds/mcp/auth.py` contains
`except TokenError, TokenBackendError:` — unparenthesized exception tuples are
valid as of PEP 758. It is not a Python 2 leftover; do not "fix" it.

**`settings_test.py` silences logging on purpose** — it filters ninja-extra's
`django.request` noise and ninja-jwt's expected ERROR on schema
`ValidationError`. If you are debugging a swallowed exception, that filter is why
you cannot see it.
