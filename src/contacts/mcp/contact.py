from typing import Annotated

from django.contrib.auth.models import AbstractBaseUser
from django.db import IntegrityError
from mcp.server.mcpserver import Resolve
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from contacts.models import Contact
from contacts.schemas import ContactCreateUpdateSchema, ContactSchema
from pds.mcp import get_current_user, mcp

DEFAULT_CONTACT_LIMIT = 50
MAX_CONTACT_LIMIT = 100


def _serialize(contact: Contact) -> ContactSchema:
    return ContactSchema.model_validate(contact)


async def _get_readable_contact(user: AbstractBaseUser, contact_id: int) -> Contact:
    contact = (
        await Contact.objects.readable_for_user(user).filter(pk=contact_id).afirst()
    )

    if contact is None:
        raise ToolError("Contact not found")

    return contact


async def _get_writable_contact(user: AbstractBaseUser, contact_id: int) -> Contact:
    contact = (
        await Contact.objects.writable_for_user(user).filter(pk=contact_id).afirst()
    )

    if contact is None:
        raise ToolError("Contact not found")

    return contact


def _limit_queryset(queryset, limit: int):
    return queryset[:limit]


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
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
    limit: Annotated[
        int,
        Field(
            ge=1,
            le=MAX_CONTACT_LIMIT,
            description="Maximum number of contacts to return.",
        ),
    ] = DEFAULT_CONTACT_LIMIT,
) -> list[ContactSchema]:
    """Search the authenticated user's contacts.

    Matching is a case-insensitive substring across name, email, phone,
    address, and notes fields. An empty query is rejected.
    """
    if not query.strip():
        raise ToolError("Search query must not be empty")

    contacts = _limit_queryset(
        Contact.objects.readable_for_user(user).search(query),
        limit,
    )

    return [_serialize(contact) async for contact in contacts]


@mcp.tool()
async def list_contacts(
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
    limit: Annotated[
        int,
        Field(
            ge=1,
            le=MAX_CONTACT_LIMIT,
            description="Maximum number of contacts to return.",
        ),
    ] = DEFAULT_CONTACT_LIMIT,
) -> list[ContactSchema]:
    """List the authenticated user's contacts, newest not guaranteed."""
    contacts = _limit_queryset(Contact.objects.readable_for_user(user), limit)

    return [_serialize(contact) async for contact in contacts]


@mcp.tool()
async def get_contact(
    contact_id: Annotated[int, Field(description="ID of the contact to retrieve.")],
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
) -> ContactSchema:
    """Get a single contact owned by the authenticated user."""
    return _serialize(await _get_readable_contact(user, contact_id))


@mcp.tool()
async def create_contact(
    payload: ContactCreateUpdateSchema,
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
) -> ContactSchema:
    """Create a contact owned by the authenticated user."""
    try:
        contact = await Contact.objects.acreate(owner=user, **payload.dict())
    except IntegrityError:
        raise ToolError("A contact with that email already exists") from None

    return _serialize(contact)


@mcp.tool()
async def update_contact(
    contact_id: Annotated[int, Field(description="ID of the contact to update.")],
    payload: ContactCreateUpdateSchema,
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
) -> ContactSchema:
    """Update a contact owned by the authenticated user.

    Omitted fields are left unchanged.
    """
    contact = await _get_writable_contact(user, contact_id)
    updates = payload.dict(exclude_unset=True)

    for attr, value in updates.items():
        setattr(contact, attr, value)

    try:
        await contact.asave()
    except IntegrityError:
        raise ToolError("A contact with that email already exists") from None

    return _serialize(contact)


@mcp.tool()
async def delete_contact(
    contact_id: Annotated[int, Field(description="ID of the contact to delete.")],
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
) -> str:
    """Permanently delete a contact owned by the authenticated user."""
    contact = await _get_writable_contact(user, contact_id)

    await contact.adelete()

    return f"Deleted contact {contact_id}"
