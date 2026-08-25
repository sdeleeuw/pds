from datetime import UTC, datetime

from django.contrib.auth import get_user_model
from django.db import models

from pds.mixins.timestamp import TimestampMixin

User = get_user_model()


class ContactQuerySet(models.QuerySet):
    def readable_for_user(self, user: User) -> models.QuerySet:
        return self.writable_for_user(user)

    def writable_for_user(self, user: User) -> models.QuerySet:
        return self.filter(owner=user)


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

    email = models.EmailField(unique=True, default="", blank=True)
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

    def __str__(self) -> str:
        return self.name
