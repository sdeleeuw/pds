from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import PatchDict, Router

from contacts.models import Contact
from contacts.schemas import ContactCreateUpdateSchema, ContactSchema

router = Router(tags=["contacts"])


@router.get("/", response=list[ContactSchema])
def list_contacts(request: HttpRequest):
    return Contact.objects.readable_for_user(request.auth)


@router.get("/{contact_id}/", response=ContactSchema)
def get_contact(request: HttpRequest, contact_id: int):
    return get_object_or_404(
        Contact.objects.readable_for_user(request.auth),
        id=contact_id,
    )


@router.post("/", response={201: ContactSchema})
def create_contact(request: HttpRequest, payload: ContactCreateUpdateSchema):
    return 201, Contact.objects.create(
        owner=request.auth,
        **payload.dict(),
    )


@router.patch("/{contact_id}/", response=ContactSchema)
def update_contact(
    request: HttpRequest,
    contact_id: int,
    payload: PatchDict[ContactCreateUpdateSchema],
):
    contact = get_object_or_404(
        Contact.objects.writable_for_user(request.auth),
        id=contact_id,
    )

    for attr, value in payload.items():
        setattr(contact, attr, value)

    contact.save()

    return contact


@router.delete("/{contact_id}/", response={204: None})
def delete_contact(request: HttpRequest, contact_id: int):
    contact = get_object_or_404(
        Contact.objects.writable_for_user(request.auth),
        id=contact_id,
    )
    contact.delete()

    return 204, None
