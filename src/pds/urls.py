from django.contrib import admin
from django.urls import path
from ninja_extra import ControllerBase, NinjaExtraAPI, api_controller
from ninja_extra.permissions import AllowAny
from ninja_jwt.authentication import AsyncJWTAuth
from ninja_jwt.controller import (
    AsyncTokenObtainPairController,
    AsyncTokenVerificationController,
)

from contacts.api import contacts_router


@api_controller("/auth", permissions=[AllowAny], tags=["auth"], auth=None)
class AuthController(
    ControllerBase,
    AsyncTokenVerificationController,
    AsyncTokenObtainPairController,
):
    pass


api = NinjaExtraAPI(auth=AsyncJWTAuth())
api.register_controllers(AuthController)
api.add_router("/contacts/", contacts_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
