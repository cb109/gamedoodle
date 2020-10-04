from django.contrib import admin
from django.urls import reverse
from django.utils.html import mark_safe

from gamedoodle.core.models import Event, Game, Vote


class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "date",
        "gameslist",
        "uuid",
        "created_at",
        "modified_at",
        "id",
    )
    search_fields = ("name", "date", "gameslist")
    autocomplete_fields = ("games",)
    readonly_fields = (
        "uuid",
        "url",
    )

    def gameslist(self, event):
        return ", ".join([game.name for game in event.games.all().order_by("name")])

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
    list_display = ("username", "event", "game", "created_at", "modified_at", "id")
    autocomplete_fields = ("event", "game")


admin.site.register(Event, EventAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Vote, VoteAdmin)
