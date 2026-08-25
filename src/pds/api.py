from ninja import NinjaAPI
from ninja.security import django_auth

from contacts.api import contacts_router

api = NinjaAPI(auth=django_auth)
api.add_router("/contacts/", contacts_router)
