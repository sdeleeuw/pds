from datetime import date

from ninja import ModelSchema, Schema
from pydantic import ConfigDict, Field

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
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    first_name: str = Field(default="", description="Given name.")
    last_name: str = Field(default="", description="Family name.")
    email: str = Field(default="", description="Email address.")
    mobile_phone: str = Field(default="", description="Mobile phone number.")
    home_phone: str = Field(default="", description="Home phone number.")
    address: str = Field(default="", description="Street address.")
    postal_code: str = Field(default="", description="Postal or ZIP code.")
    city: str = Field(default="", description="City.")
    region: str = Field(default="", description="State, province, or region.")
    country: str = Field(default="", description="Country.")
    date_of_birth: date | None = Field(
        default=None,
        description="Date of birth (YYYY-MM-DD).",
    )
    notes: str = Field(default="", description="Free-form notes about the contact.")
