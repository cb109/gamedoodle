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
    date = models.DateField(default=date.today)
    games = models.ManyToManyField("SteamGame", null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.name} {self.date.strftime(settings.DATE_FORMAT)}"


class SteamGame(TimestampedMixin, models.Model):
    """A Game on Steam."""

    name = models.CharField(max_length=256)
    appid = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.appid})"


class Vote(TimestampedMixin, models.Model):
    """A User votes to play a Game during a certain Event."""

    event = models.ForeignKey("Event", on_delete=models.CASCADE)
    game = models.ForeignKey("SteamGame", on_delete=models.CASCADE)
    username = models.CharField(max_length=256)

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
