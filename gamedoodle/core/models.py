from datetime import date

from django.db import models


class TimestampedMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Event(TimestampedMixin, models.Model):
    """A date on which to play certain games that can be voted for."""

    name = models.CharField(max_length=256)
    date = models.DateField(default=date.today)
    games = models.ManyToManyField("SteamGame", null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.name} {self.date.strftime('%d.%m.%Y')}"


class SteamGame(TimestampedMixin, models.Model):
    """A Game on Steam."""

    name = models.CharField(max_length=256)
    appid = models.PositiveIntegerField()


class Vote(TimestampedMixin, models.Model):
    """A User votes to play a Game during a certain Event."""

    event = models.ForeignKey("Event", on_delete=models.CASCADE)
    game = models.ForeignKey("SteamGame", on_delete=models.CASCADE)
    username = models.CharField(max_length=256)
