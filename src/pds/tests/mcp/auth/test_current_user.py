from django.test import TestCase
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from mcp.server.mcpserver.exceptions import ToolError

from pds.mcp import as_user, get_current_user
from pds.tests.fixtures import create_user


class GetCurrentUserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(username="alice", email="alice@example.com")
        cls.other_user = create_user(username="bob", email="bob@example.com")
        cls.inactive_user = create_user(
            username="inactive",
            email="inactive@example.com",
        )
        cls.inactive_user.is_active = False
        cls.inactive_user.save()

    def _set_access_token(self, *, subject: str, token: str = "test-token"):
        access = AccessToken(
            token=token,
            client_id=subject,
            scopes=[],
            subject=subject,
        )
        return auth_context_var.set(AuthenticatedUser(access))

    async def test_resolves_active_user_from_access_token(self):
        # Given: an authenticated bearer token for an active user
        ctx_token = self._set_access_token(subject=str(self.user.pk))

        try:
            # When: resolving the current user
            user = await get_current_user()

            # Then: the token subject is returned
            self.assertEqual(user.pk, self.user.pk)
        finally:
            auth_context_var.reset(ctx_token)

    async def test_unknown_subject_raises(self):
        # Given: a bearer token whose subject does not match any user
        ctx_token = self._set_access_token(subject="999999")

        try:
            # When/Then: resolving the current user fails
            with self.assertRaises(ToolError):
                await get_current_user()
        finally:
            auth_context_var.reset(ctx_token)

    async def test_inactive_subject_raises(self):
        # Given: a bearer token for an inactive user
        ctx_token = self._set_access_token(subject=str(self.inactive_user.pk))

        try:
            # When/Then: resolving the current user fails
            with self.assertRaises(ToolError):
                await get_current_user()
        finally:
            auth_context_var.reset(ctx_token)

    async def test_no_credential_raises(self):
        # Given: no bearer token and no as_user context

        # When/Then: resolving the current user fails
        with self.assertRaises(ToolError):
            await get_current_user()

    async def test_as_user_resolves(self):
        # Given: an in-process as_user context

        # When: resolving the current user
        with as_user(self.user):
            user = await get_current_user()

        # Then: the context user is returned
        self.assertEqual(user.pk, self.user.pk)

    async def test_bearer_token_wins_over_as_user(self):
        # Given: both a bearer token and an as_user context for different users
        ctx_token = self._set_access_token(subject=str(self.user.pk))

        try:
            # When: resolving the current user inside as_user for another user
            with as_user(self.other_user):
                user = await get_current_user()

            # Then: the bearer token subject wins
            self.assertEqual(user.pk, self.user.pk)
        finally:
            auth_context_var.reset(ctx_token)
