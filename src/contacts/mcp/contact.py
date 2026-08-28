from datetime import date
from typing import Annotated

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from mcp.server.mcpserver import Resolve
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from contacts.models import Contact
from contacts.schemas import ContactCreateUpdateSchema, ContactSchema
from pds.mcp.annotations import (
    CREATE_ANNOTATIONS,
    DELETE_ANNOTATIONS,
    READ_ONLY_ANNOTATIONS,
    UPDATE_ANNOTATIONS,
)
from pds.mcp.auth import get_current_user
from pds.mcp.server import mcp

User = get_user_model()

DEFAULT_CONTACT_LIMIT = 50
MAX_CONTACT_LIMIT = 100


def get_queryset(user: User, for_write: bool):
    if for_write:
        return Contact.objects.writable_for_user(user)

    return Contact.objects.readable_for_user(user)


async def get_object(user: User, pk: int, for_write: bool) -> Contact:
    contact = await get_queryset(user=user, for_write=for_write).filter(pk=pk).afirst()

    if contact is None:
        raise ToolError("Contact not found")

    return contact


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
async def search_contacts(
    query: Annotated[
        str,
        Field(
            description=(
                "Case-insensitive substring matched against first name, last "
                "name, email, phone numbers, address, postal code, city, "
                "region, country, and notes."
            )
        ),
    ],
    limit: Annotated[
        int,
        Field(
            ge=1,
            le=MAX_CONTACT_LIMIT,
            description="Maximum number of contacts to return.",
        ),
    ] = DEFAULT_CONTACT_LIMIT,
    *,
    user: Annotated[User, Resolve(get_current_user)],
) -> list[ContactSchema]:
    """Search the authenticated user's contacts by a non-empty substring.

    Matching is case-insensitive across first_name, last_name, email, phone
    numbers, address, and notes. Use list_contacts to page without a query,
    and get_contact when you already have an id. Returned name and age are
    computed and read-only.
    """

    if not query.strip():
        raise ToolError("Search query must not be empty")

    contacts = get_queryset(user=user, for_write=False).search(query)[:limit]

    return [ContactSchema.model_validate(contact) async for contact in contacts]


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
async def list_contacts(
    limit: Annotated[
        int,
        Field(
            ge=1,
            le=MAX_CONTACT_LIMIT,
            description="Maximum number of contacts to return.",
        ),
    ] = DEFAULT_CONTACT_LIMIT,
    *,
    user: Annotated[User, Resolve(get_current_user)],
) -> list[ContactSchema]:
    """List the authenticated user's contacts, newest not guaranteed.

    Use search_contacts to filter by a substring, and get_contact for a
    single id. Returned name and age are computed and read-only.
    """
    contacts = get_queryset(user=user, for_write=False)[:limit]
    return [ContactSchema.model_validate(contact) async for contact in contacts]


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
async def get_contact(
    contact_id: Annotated[int, Field(description="ID of the contact to retrieve.")],
    *,
    user: Annotated[User, Resolve(get_current_user)],
) -> ContactSchema:
    """Get a single contact owned by the authenticated user.

    Use search_contacts or list_contacts to find an id. Returned name and
    age are computed and read-only.
    """
    obj = await get_object(user=user, pk=contact_id, for_write=False)
    return ContactSchema.model_validate(obj)


def _field_with_desc(name: str):
    return Field(description=ContactCreateUpdateSchema.model_fields[name].description)


@mcp.tool(annotations=CREATE_ANNOTATIONS)
async def create_contact(
    first_name: Annotated[str, _field_with_desc("first_name")] = "",
    last_name: Annotated[str, _field_with_desc("last_name")] = "",
    email: Annotated[str, _field_with_desc("email")] = "",
    mobile_phone: Annotated[str, _field_with_desc("mobile_phone")] = "",
    home_phone: Annotated[str, _field_with_desc("home_phone")] = "",
    address: Annotated[str, _field_with_desc("address")] = "",
    postal_code: Annotated[str, _field_with_desc("postal_code")] = "",
    city: Annotated[str, _field_with_desc("city")] = "",
    region: Annotated[str, _field_with_desc("region")] = "",
    country: Annotated[str, _field_with_desc("country")] = "",
    date_of_birth: Annotated[date | None, _field_with_desc("date_of_birth")] = None,
    notes: Annotated[str, _field_with_desc("notes")] = "",
    *,
    user: Annotated[User, Resolve(get_current_user)],
) -> ContactSchema:
    """Create a contact owned by the authenticated user.

    Pass first_name and last_name separately; name is a read-only computed
    field on the result. Phone numbers go in mobile_phone or home_phone,
    not phone. Age is computed from date_of_birth and is also read-only.
    """

    payload = ContactCreateUpdateSchema.model_validate(
        {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "mobile_phone": mobile_phone,
            "home_phone": home_phone,
            "address": address,
            "postal_code": postal_code,
            "city": city,
            "region": region,
            "country": country,
            "date_of_birth": date_of_birth,
            "notes": notes,
        }
    )

    try:
        contact = await Contact.objects.acreate(owner=user, **payload.dict())
    except IntegrityError:
        raise ToolError("A contact with that email already exists") from None

    return ContactSchema.model_validate(contact)


@mcp.tool(annotations=UPDATE_ANNOTATIONS)
async def update_contact(
    contact_id: Annotated[int, Field(description="ID of the contact to update.")],
    first_name: Annotated[str | None, _field_with_desc("first_name")] = None,
    last_name: Annotated[str | None, _field_with_desc("last_name")] = None,
    email: Annotated[str | None, _field_with_desc("email")] = None,
    mobile_phone: Annotated[str | None, _field_with_desc("mobile_phone")] = None,
    home_phone: Annotated[str | None, _field_with_desc("home_phone")] = None,
    address: Annotated[str | None, _field_with_desc("address")] = None,
    postal_code: Annotated[str | None, _field_with_desc("postal_code")] = None,
    city: Annotated[str | None, _field_with_desc("city")] = None,
    region: Annotated[str | None, _field_with_desc("region")] = None,
    country: Annotated[str | None, _field_with_desc("country")] = None,
    date_of_birth: Annotated[date | None, _field_with_desc("date_of_birth")] = None,
    notes: Annotated[str | None, _field_with_desc("notes")] = None,
    *,
    user: Annotated[User, Resolve(get_current_user)],
) -> ContactSchema:
    """Update a contact owned by the authenticated user.

    Omitted fields are left unchanged; pass an empty string to clear a text
    field. Pass first_name and last_name separately; name is read-only.
    Phone numbers go in mobile_phone or home_phone, not phone.
    """

    contact = await get_object(user=user, pk=contact_id, for_write=True)
    updates = ContactCreateUpdateSchema.model_validate(
        {
            name: value
            for name, value in {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "mobile_phone": mobile_phone,
                "home_phone": home_phone,
                "address": address,
                "postal_code": postal_code,
                "city": city,
                "region": region,
                "country": country,
                "date_of_birth": date_of_birth,
                "notes": notes,
            }.items()
            if value is not None
        }
    ).dict(exclude_unset=True)

    for attr, value in updates.items():
        setattr(contact, attr, value)

    try:
        await contact.asave()
    except IntegrityError:
        raise ToolError("A contact with that email already exists") from None

    return ContactSchema.model_validate(contact)


@mcp.tool(annotations=DELETE_ANNOTATIONS)
async def delete_contact(
    contact_id: Annotated[int, Field(description="ID of the contact to delete.")],
    *,
    user: Annotated[User, Resolve(get_current_user)],
) -> str:
    """Permanently delete a contact owned by the authenticated user."""

    contact = await get_object(user=user, pk=contact_id, for_write=True)

    await contact.adelete()

    return f"Deleted contact {contact_id}"
