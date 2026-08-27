from datetime import UTC, datetime

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q

from pds.mixins.timestamp import TimestampMixin

User = get_user_model()


class ContactQuerySet(models.QuerySet):
    def readable_for_user(self, user: User) -> models.QuerySet:
        return self.writable_for_user(user)

    def writable_for_user(self, user: User) -> models.QuerySet:
        return self.filter(owner=user)

    def search(self, query: str) -> models.QuerySet:
        query = query.strip()

        if not query:
            return self

        return self.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(mobile_phone__icontains=query)
            | Q(home_phone__icontains=query)
            | Q(address__icontains=query)
            | Q(postal_code__icontains=query)
            | Q(city__icontains=query)
            | Q(region__icontains=query)
            | Q(country__icontains=query)
            | Q(notes__icontains=query)
        )


class Contact(TimestampMixin, models.Model):
    first_name = models.CharField(max_length=255, default="", blank=True)
    last_name = models.CharField(max_length=255, default="", blank=True)

    @property
    def name(self) -> str:
        return " ".join(
            part.strip()
            for part in (self.first_name, self.last_name)
            if part and part.strip()
        )

    email = models.EmailField(default="", blank=True)
    mobile_phone = models.CharField(max_length=255, default="", blank=True)
    home_phone = models.CharField(max_length=255, default="", blank=True)

    address = models.TextField(default="", blank=True)
    postal_code = models.CharField(max_length=255, default="", blank=True)
    city = models.CharField(max_length=255, default="", blank=True)
    region = models.CharField(max_length=255, default="", blank=True)
    country = models.CharField(max_length=255, default="", blank=True)

    date_of_birth = models.DateField(null=True, blank=True)

    notes = models.TextField(default="", blank=True)

    @property
    def age(self) -> int | None:
        if self.date_of_birth is None:
            return None

        today = datetime.now(tz=UTC).date()
        years = today.year - self.date_of_birth.year
        birthday = (self.date_of_birth.month, self.date_of_birth.day)

        if (today.month, today.day) < birthday:
            years -= 1

        return years

    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="contacts",
    )

    objects = ContactQuerySet.as_manager()

    class Meta:
        db_table = "contacts"
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "email"],
                condition=~Q(email=""),
                name="contacts_unique_owner_email",
            ),
        ]

    def __str__(self) -> str:
        return self.name
