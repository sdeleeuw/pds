from datetime import date

from django.contrib.auth import get_user_model

from contacts.models import Contact

User = get_user_model()


def create_contact(owner: User, **kwargs) -> Contact:
    defaults = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "mobile_phone": "+31612345678",
        "home_phone": "",
        "address": "Main Street 1",
        "postal_code": "1234AB",
        "city": "Amsterdam",
        "region": "Noord-Holland",
        "country": "NL",
        "date_of_birth": date(1990, 5, 15),
        "notes": "A test contact",
    }
    defaults.update(kwargs)

    return Contact.objects.create(owner=owner, **defaults)
