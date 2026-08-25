from django.http import HttpRequest
from django.shortcuts import get_object_or_404
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


def get_object(request: HttpRequest, pk: int):
    return get_object_or_404(get_queryset(request), pk=pk)


@router.get("/", response=list[ContactSchema])
async def list_contacts(request: HttpRequest):
    return get_queryset(request)


@router.get("/{contact_id}/", response=ContactSchema)
async def get_contact(request: HttpRequest, contact_id: int):
    return get_object(request, contact_id)


@router.post("/", response={201: ContactSchema})
async def create_contact(request: HttpRequest, payload: ContactCreateUpdateSchema):
    return 201, Contact.objects.create(
        owner=request.auth,
        **payload.dict(),
    )


@router.patch("/{contact_id}/", response=ContactSchema)
async def update_contact(
    request: HttpRequest,
    contact_id: int,
    payload: PatchDict[ContactCreateUpdateSchema],
):
    contact = get_object(request, contact_id)

    for attr, value in payload.items():
        setattr(contact, attr, value)

    contact.save()

    return contact


@router.delete("/{contact_id}/", response={204: None})
async def delete_contact(request: HttpRequest, contact_id: int):
    contact = get_object(request, contact_id)
    contact.delete()

    return 204, None
