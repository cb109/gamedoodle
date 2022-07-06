import uuid
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class TimestampedMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Event(TimestampedMixin, models.Model):
    """A date on which to play certain games that can be voted for."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    details = models.TextField(default="", blank=True)
    date = models.DateField(default=date.today, blank=True, null=True)
    games = models.ManyToManyField("Game", blank=True)
    read_only = models.BooleanField(default=False)
    listed = models.BooleanField(default=True)

    def __str__(self):
        date_str = "no date yet"
        if self.date:
            date_str = self.date.strftime(settings.DATE_FORMAT)
        return f"{self.name} {date_str}"

    @property
    def is_writable(self):
        return not self.read_only


class EventSubscription(TimestampedMixin, models.Model):
    """A User wants to receive activity notifications about an Event."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    email = models.EmailField(max_length=254)
    username = models.CharField(max_length=256, default="", blank=True)
    active = models.BooleanField(default=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    def __str__(self):
        return (
            f"{self.email} ({self.username})-> "
            f"{self.event.name} [{'x' if self.active else ' '}]"
        )


class Game(TimestampedMixin, models.Model):
    """A Game on Steam."""

    name = models.CharField(max_length=256)
    appid = models.PositiveIntegerField(null=True, blank=True, default=None)
    image_url = models.CharField(max_length=256, blank=True, default="")
    store_url = models.CharField(max_length=256, blank=True, default="")
    is_free = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.appid})"


class Vote(TimestampedMixin, models.Model):
    """A User votes to play a Game during a certain Event."""

    event = models.ForeignKey("Event", on_delete=models.CASCADE)
    game = models.ForeignKey("Game", on_delete=models.CASCADE)
    username = models.CharField(max_length=256)
    is_superlike = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "game", "username"], name="unique vote"
            )
        ]

    def __str__(self):
        return f"{self.username} wants to play '{self.game}' during '{self.event}'"

    def save(self, *args, **kwargs):
        if not self.game in self.event.games.all():
            raise ValidationError(
                f"Can only vote for game that belongs to event {self.event}, "
                f"but tried to vote for {self.game}"
            )
        super().save(*args, **kwargs)


class SentMail(TimestampedMixin, models.Model):
    """An email that has been sent to someone."""

    sender = models.CharField(max_length=256)
    recipient = models.CharField(max_length=256)
    subject = models.TextField()
    body = models.TextField()
    html = models.TextField()
