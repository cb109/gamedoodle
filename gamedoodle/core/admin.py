from django.contrib import admin

from gamedoodle.core.models import Event, SteamGame, Vote


class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "gameslist", "created_at", "modified_at", "id")

    def gameslist(self, event):
        return ", ".join([game.name for game in event.games.all().order_by("name")])


admin.site.register(Event, EventAdmin)
admin.site.register(SteamGame)
admin.site.register(Vote)
