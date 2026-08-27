from django.test import TestCase
from mcp.server.mcpserver.exceptions import ToolError

from pds.mcp import get_current_user
from pds.tests.fixtures import create_user
from pds.tests.mcp.auth.helpers import authenticated_as, mcp_access_token


class GetCurrentUserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(username="alice", email="alice@example.com")
        cls.inactive_user = create_user(
            username="inactive",
            email="inactive@example.com",
        )
        cls.inactive_user.is_active = False
        cls.inactive_user.save()

    async def test_resolves_active_user_from_access_token(self):
        # Given: an authenticated bearer token for an active user

        # When: resolving the current user
        with authenticated_as(self.user):
            user = await get_current_user()

        # Then: the token subject is returned
        self.assertEqual(user.pk, self.user.pk)

    async def test_unknown_subject_raises(self):
        # Given: a bearer token whose subject does not match any user

        # When/Then: resolving the current user fails
        with mcp_access_token(subject="999999"):
            with self.assertRaises(ToolError):
                await get_current_user()

    async def test_inactive_subject_raises(self):
        # Given: a bearer token for an inactive user

        # When/Then: resolving the current user fails
        with authenticated_as(self.inactive_user):
            with self.assertRaises(ToolError):
                await get_current_user()

    async def test_no_credential_raises(self):
        # Given: no bearer token

        # When/Then: resolving the current user fails
        with self.assertRaises(ToolError):
            await get_current_user()

    async def test_empty_subject_raises(self):
        # Given: a bearer token with an empty subject

        # When/Then: resolving the current user fails closed
        with mcp_access_token(subject=""):
            with self.assertRaises(ToolError):
                await get_current_user()
