from django.apps import AppConfig


class ContactsConfig(AppConfig):
    name = "contacts"

    def ready(self) -> None:
        import contacts.mcp.contact  # noqa: F401
