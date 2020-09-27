from django.contrib import admin

from gamedoodle.core.models import Event, SteamGame, Vote


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
    readonly_fields = ("uuid",)

    def gameslist(self, event):
        return ", ".join([game.name for game in event.games.all().order_by("name")])


class SteamGameAdmin(admin.ModelAdmin):
    list_display = ("name", "appid", "created_at", "modified_at", "id")
    search_fields = ("name", "appid")


class VoteAdmin(admin.ModelAdmin):
    list_display = ("username", "event", "game", "created_at", "modified_at", "id")
    autocomplete_fields = ("event", "game")


admin.site.register(Event, EventAdmin)
admin.site.register(SteamGame, SteamGameAdmin)
admin.site.register(Vote, VoteAdmin)
