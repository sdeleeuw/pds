from datetime import date

from ninja import ModelSchema, Schema

from contacts.models import Contact


class ContactSchema(ModelSchema):
    name: str
    age: int | None

    class Meta:
        model = Contact
        fields = (
            "id",
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
            "date_of_birth",
            "notes",
            "created_at",
            "updated_at",
        )


class ContactCreateUpdateSchema(Schema):
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    mobile_phone: str = ""
    home_phone: str = ""
    address: str = ""
    postal_code: str = ""
    city: str = ""
    region: str = ""
    country: str = ""
    date_of_birth: date | None = None
    notes: str = ""
