from django.contrib import admin
from django.urls import reverse
from django.utils.html import mark_safe

from gamedoodle.core.models import (
    Comment,
    Event,
    EventGame,
    EventSubscription,
    Game,
    SentMail,
    Vote,
)


class SentMailAdmin(admin.ModelAdmin):
    list_display = (
        "recipient",
        "subject",
        "body_html",
    )

    @mark_safe
    def body_html(self, sentmail):
        return sentmail.html


class EventSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "active",
        "email",
        "username",
    )


class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "date",
        "writable",
        "listed",
        "gameslist",
        "uuid",
        "created_at",
        "modified_at",
        "url",
        "id",
    )
    search_fields = ("name", "date", "gameslist")
    autocomplete_fields = ("games",)
    readonly_fields = (
        "uuid",
        "url",
    )

    def writable(self, event):
        return event.is_writable

    writable.boolean = True

    @mark_safe
    def gameslist(self, event):
        html = "<ul>"
        for eventgame in EventGame.objects.filter(event=event).order_by("game__name"):
            suffix = ""
            if eventgame.added_by_username:
                suffix = f" <small style='color: grey'>added by <b>"
                suffix += f"  {eventgame.added_by_username}</b></small>"
            html += f"<li><a href='{eventgame.game.store_url}' target='_blank'>"
            html += f"  {eventgame.game.name}"
            html += f"</a>{suffix}</li>"
        html += "</ul>"
        return html

    @mark_safe
    def url(self, event):
        url = reverse("event-detail", kwargs={"uuid": event.uuid})
        return f"<a href='{url}' target='_blank'>{url}</a>"


class GameAdmin(admin.ModelAdmin):
    list_display = ("name", "appid", "created_at", "modified_at", "id")
    search_fields = ("name", "appid")

    @mark_safe
    def image(self, game):
        if not game.image_url.strip():
            return ""

        url = game.image_url
        return (
            f"<img src='{url}' style='width: 100%; height: auto; "
            "max-width: 480px; max-height: 480px'>"
        )


class VoteAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "event",
        "game",
        "is_superlike",
        "created_at",
        "modified_at",
        "id",
    )
    autocomplete_fields = ("event", "game")


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "event",
        "game",
        "text",
        "visible",
        "created_at",
        "modified_at",
        "id",
    )
    autocomplete_fields = ("event", "game")

    def visible(self, comment):
        return not comment.softdeleted

    visible.boolean = True


admin.site.site_header = "gamedoodle admin"

admin.site.register(Comment, CommentAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(EventSubscription, EventSubscriptionAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(SentMail, SentMailAdmin)
admin.site.register(Vote, VoteAdmin)
