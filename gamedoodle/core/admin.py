from django.contrib import admin
from django.urls import reverse
from django.utils.html import mark_safe

from gamedoodle.core.models import Event, EventSubscription, Game, Vote, SentMail


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
        lis = "".join(
            [
                f"<li><a href='{game.store_url}' target='_blank'>{game.name}</a></li>"
                for game in event.games.all().order_by("name")
            ]
        )
        return f"<ul>{lis}<ul>"

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


admin.site.site_header = "gamedoodle admin"

admin.site.register(Event, EventAdmin)
admin.site.register(EventSubscription, EventSubscriptionAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(SentMail, SentMailAdmin)
admin.site.register(Vote, VoteAdmin)
