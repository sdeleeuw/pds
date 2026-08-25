from django.contrib import admin

from contacts.models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "mobile_phone",
        "owner",
        "updated_at",
    )

    list_filter = ("owner", "created_at", "updated_at")

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "mobile_phone",
        "home_phone",
        "address",
        "postal_code",
        "city",
        "region",
        "country",
    )
