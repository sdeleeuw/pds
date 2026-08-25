from typing import Annotated

from django.contrib.auth.models import AbstractBaseUser
from mcp.server.mcpserver import Resolve
from mcp.server.mcpserver.exceptions import ToolError

from contacts.models import Contact
from contacts.schemas import ContactCreateUpdateSchema, ContactSchema
from pds.mcp import get_current_user, mcp


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


@mcp.tool()
async def search_contacts(
    query: str,
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
) -> list[ContactSchema]:
    contacts = Contact.objects.readable_for_user(user).search(query)

    return [_serialize(contact) async for contact in contacts]


@mcp.tool()
async def list_contacts(
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
) -> list[ContactSchema]:
    contacts = Contact.objects.readable_for_user(user)

    return [_serialize(contact) async for contact in contacts]


@mcp.tool()
async def get_contact(
    contact_id: int,
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
) -> ContactSchema:
    return _serialize(await _get_readable_contact(user, contact_id))


@mcp.tool()
async def create_contact(
    payload: ContactCreateUpdateSchema,
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
) -> ContactSchema:
    contact = await Contact.objects.acreate(owner=user, **payload.dict())

    return _serialize(contact)


@mcp.tool()
async def update_contact(
    contact_id: int,
    payload: ContactCreateUpdateSchema,
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
) -> ContactSchema:
    contact = await _get_writable_contact(user, contact_id)
    updates = payload.dict(exclude_unset=True)

    for attr, value in updates.items():
        setattr(contact, attr, value)

    await contact.asave()

    return _serialize(contact)


@mcp.tool()
async def delete_contact(
    contact_id: int,
    user: Annotated[AbstractBaseUser, Resolve(get_current_user)],
) -> str:
    contact = await _get_writable_contact(user, contact_id)

    await contact.adelete()

    return f"Deleted contact {contact_id}"
