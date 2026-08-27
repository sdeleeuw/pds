from asgiref.sync import sync_to_async
from django.contrib import admin
from django.http import HttpRequest
from django.urls import path
from ninja import Schema
from ninja_extra import (
    ControllerBase,
    NinjaExtraAPI,
    api_controller,
    http_delete,
    http_post,
)
from ninja_extra.permissions import AllowAny
from ninja_jwt.authentication import AsyncJWTAuth
from ninja_jwt.controller import (
    AsyncTokenObtainPairController,
    AsyncTokenVerificationController,
)

from contacts.api import contacts_router
from pds.mcp.tokens import issue_mcp_token, revoke_mcp_tokens_for_user


class MCPTokenOut(Schema):
    token: str


@api_controller("/auth", permissions=[AllowAny], tags=["auth"], auth=None)
class AuthController(
    ControllerBase,
    AsyncTokenVerificationController,
    AsyncTokenObtainPairController,
):
    @http_post(
        "/mcp-token",
        auth=AsyncJWTAuth(),
        response=MCPTokenOut,
        url_name="mcp_token_create",
    )
    async def create_mcp_token(self, request: HttpRequest) -> MCPTokenOut:
        token = await sync_to_async(issue_mcp_token)(request.auth)
        return MCPTokenOut(token=str(token))

    @http_delete(
        "/mcp-token",
        auth=AsyncJWTAuth(),
        response={204: None},
        url_name="mcp_token_revoke",
    )
    async def revoke_mcp_tokens(self, request: HttpRequest):
        await sync_to_async(revoke_mcp_tokens_for_user)(request.auth)
        return 204, None


api = NinjaExtraAPI(auth=AsyncJWTAuth())
api.register_controllers(AuthController)
api.add_router("/contacts/", contacts_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
