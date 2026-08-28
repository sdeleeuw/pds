from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from ninja import PatchDict, Router

from contacts.models import Contact
from contacts.schemas import ContactCreateUpdateSchema, ContactSchema

router = Router(tags=["contacts"])


def get_queryset(request: HttpRequest):
    user = request.auth

    if request.method in ("PUT", "PATCH", "DELETE"):
        return Contact.objects.writable_for_user(user)
    else:
        return Contact.objects.readable_for_user(user)


async def get_object(request: HttpRequest, pk: int):
    return await aget_object_or_404(get_queryset(request), pk=pk)


@router.get("/", response=list[ContactSchema])
async def list_contacts(request: HttpRequest):
    """List contacts.

    Returned name and age are computed and read-only.
    """
    return [contact async for contact in get_queryset(request)]


@router.get("/{contact_id}/", response=ContactSchema)
async def get_contact(request: HttpRequest, contact_id: int):
    """Get a single contact.

    Returned name and age are computed and read-only.
    """
    return await get_object(request, contact_id)


@router.post("/", response={201: ContactSchema})
async def create_contact(request: HttpRequest, payload: ContactCreateUpdateSchema):
    """Create a contact.

    Returned name and age are computed and read-only.
    """
    return 201, await Contact.objects.acreate(
        owner=request.auth,
        **payload.dict(),
    )


@router.patch("/{contact_id}/", response=ContactSchema)
async def update_contact(
    request: HttpRequest,
    contact_id: int,
    payload: PatchDict[ContactCreateUpdateSchema],
):
    """Update a contact.

    Omitted fields are left unchanged; pass an empty string to clear a text
    field. Returned name and age are computed and read-only.
    """
    contact = await get_object(request, contact_id)

    for attr, value in payload.items():
        setattr(contact, attr, value)

    await contact.asave()

    return contact


@router.delete("/{contact_id}/", response={204: None})
async def delete_contact(request: HttpRequest, contact_id: int):
    """Permanently delete a contact."""
    contact = await get_object(request, contact_id)

    await contact.adelete()

    return 204, None
