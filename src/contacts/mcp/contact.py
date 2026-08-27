from typing import Annotated

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from mcp.server.mcpserver import Resolve
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from contacts.models import Contact
from contacts.schemas import ContactCreateUpdateSchema, ContactSchema
from pds.mcp import get_current_user, mcp

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


@mcp.tool()
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
    """Search the authenticated user's contacts.

    Matching is a case-insensitive substring across name, email, phone,
    address, and notes fields. An empty query is rejected.
    """

    if not query.strip():
        raise ToolError("Search query must not be empty")

    contacts = get_queryset(user, False).search(query)[:limit]

    return [ContactSchema.model_validate(contact) async for contact in contacts]


@mcp.tool()
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
    """List the authenticated user's contacts, newest not guaranteed."""
    contacts = get_queryset(user, False)[:limit]
    return [ContactSchema.model_validate(contact) async for contact in contacts]


@mcp.tool()
async def get_contact(
    contact_id: Annotated[int, Field(description="ID of the contact to retrieve.")],
    *,
    user: Annotated[User, Resolve(get_current_user)],
) -> ContactSchema:
    """Get a single contact owned by the authenticated user."""
    return ContactSchema.model_validate(await get_object(user, contact_id, False))


@mcp.tool()
async def create_contact(
    payload: ContactCreateUpdateSchema,
    *,
    user: Annotated[User, Resolve(get_current_user)],
) -> ContactSchema:
    """Create a contact owned by the authenticated user."""

    try:
        contact = await Contact.objects.acreate(owner=user, **payload.dict())
    except IntegrityError:
        raise ToolError("A contact with that email already exists") from None

    return ContactSchema.model_validate(contact)


@mcp.tool()
async def update_contact(
    contact_id: Annotated[int, Field(description="ID of the contact to update.")],
    payload: ContactCreateUpdateSchema,
    *,
    user: Annotated[User, Resolve(get_current_user)],
) -> ContactSchema:
    """Update a contact owned by the authenticated user.

    Omitted fields are left unchanged.
    """

    contact = await get_object(user, contact_id, True)
    updates = payload.dict(exclude_unset=True)

    for attr, value in updates.items():
        setattr(contact, attr, value)

    try:
        await contact.asave()
    except IntegrityError:
        raise ToolError("A contact with that email already exists") from None

    return ContactSchema.model_validate(contact)


@mcp.tool()
async def delete_contact(
    contact_id: Annotated[int, Field(description="ID of the contact to delete.")],
    *,
    user: Annotated[User, Resolve(get_current_user)],
) -> str:
    """Permanently delete a contact owned by the authenticated user."""

    contact = await get_object(user, contact_id, True)

    await contact.adelete()

    return f"Deleted contact {contact_id}"
