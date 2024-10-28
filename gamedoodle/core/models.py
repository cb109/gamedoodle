import uuid
from datetime import timedelta, date
from functools import partial
from typing import List
from typing import Optional

import bleach
from bleach import Cleaner
from bleach.linkifier import LinkifyFilter
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

COMMENT_IS_NEW_THRESHOLD_MINUTES = 60


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
    games = models.ManyToManyField(
        "Game", blank=True, related_name="games", through="EventGame"
    )
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

    @property
    def usernames(self):
        return sorted(
            [
                username
                for username in (
                    self.vote_set.all()
                    .values_list("username", flat=True)
                    .distinct()
                )
            ],
            key=lambda username: username.lower()
        )


class EventGame(TimestampedMixin, models.Model):
    event = models.ForeignKey("Event", on_delete=models.CASCADE)
    game = models.ForeignKey("Game", on_delete=models.CASCADE)
    added_by_username = models.CharField(max_length=256, default="", blank=True)


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

    def get_votes_for_event(self, event: Event):
        return Vote.objects.filter(game=self, event=event).order_by("username")

    def get_comments_for_event(self, event: Event) -> List[Event]:
        return get_comments(event=event, game=self)

    def get_added_by_username_for_event(self, event) -> str:
        return EventGame.objects.get(event=event, game=self).added_by_username


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


class Comment(TimestampedMixin, models.Model):
    event = models.ForeignKey("Event", on_delete=models.CASCADE)

    game = models.ForeignKey(
        "Game", on_delete=models.CASCADE, null=True, blank=True, default=None
    )
    """If the comment is not linked to a Game, it's a global Event comment."""

    username = models.CharField(max_length=256)
    text = models.TextField()
    softdeleted = models.BooleanField(default=False)

    def __str__(self):
        if self.game:
            return f"{self.username} commented on '{self.game}' during '{self.event}'"
        return f"{self.username} commented during '{self.event}'"

    def save(self, *args, **kwargs):
        if self.game and not self.game in self.event.games.all():
            raise ValidationError(
                f"Can only comment on game that belongs to event {self.event}, "
                f"but tried to comment on {self.game}"
            )
        super().save(*args, **kwargs)

    @property
    def is_new(self):
        """Created within the last hour."""
        return self.created_at >= timezone.now() - timedelta(
            hours=COMMENT_IS_NEW_THRESHOLD_MINUTES / 60
        )

    @property
    def text_as_html(self):
        """Clean, linkify and prevent link overflow.

        See:

        - https://bleach.readthedocs.io/en/latest/linkify.html#linkify-linkifyfilter
        - https://github.com/mozilla/bleach/blob/24c21bb8a20d0c72a44fee81c290f41774e8384e/bleach/callbacks.py

        """

        def break_word(attrs, new=False):
            attrs[(None, "style")] = "word-break: break-word"
            return attrs

        callbacks = bleach.linkifier.DEFAULT_CALLBACKS + [break_word]
        filters = [partial(LinkifyFilter, callbacks=callbacks)]
        return Cleaner(filters=filters).clean(self.text)

    @property
    def short_preview(self):
        max_chars = 140
        shortened = self.text[:max_chars]
        if shortened != self.text:
            shortened += "..."
        return shortened


class SentMail(TimestampedMixin, models.Model):
    """An email that has been sent to someone."""

    sender = models.CharField(max_length=256)
    recipient = models.CharField(max_length=256)
    subject = models.TextField()
    body = models.TextField()
    html = models.TextField()


def get_comments(
    event: Event,
    game: Optional[Game] = None,
    ignore_softdeleted: bool = True,
    augment_alignment: bool = True
) -> List[Comment]:
    comments = Comment.objects.filter(event=event, game=game)
    if ignore_softdeleted:
        comments = comments.exclude(softdeleted=True)
    comments = list(comments.order_by("created_at"))

    if augment_alignment:
        comments = comments
        current_alignment: str = "left"
        for i, comment in enumerate(comments):
            try:
                previous_comment = comments[i - 1]
            except IndexError:
                previous_comment = None
            if previous_comment and previous_comment.username == comment.username:
                current_alignment = getattr(
                    previous_comment, "alignment", current_alignment
                )

            comment.alignment = current_alignment

            if current_alignment == "left":
                current_alignment = "right"
            else:
                current_alignment = "left"
    return comments
