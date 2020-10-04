from django.conf import settings
from django.core.management.base import BaseCommand

import requests
from gamedoodle.core.models import Game

STEAM_API_URL_GET_APP_LIST = (
    "https://api.steampowered.com/ISteamApps/GetAppList/v0002/"
    f"?key={settings.STEAM_API_KEY}&format=json"
)

STEAM_STORE_PAGE_BASE_URL = "https://store.steampowered.com/app/"  # + appid


class Command(BaseCommand):
    def handle(self, *args, **options):
        response = requests.get(STEAM_API_URL_GET_APP_LIST)
        data = response.json()
        apps = data["applist"]["apps"]

        if Game.objects.count() == 0:
            games = [Game(appid=app["appid"], name=app["name"]) for app in apps]
            Game.objects.bulk_create(games)
        else:
            for i, app in enumerate(apps):
                print(i + 1, len(apps))
                Game.objects.get_or_create(
                    appid=app["appid"],
                    name=app["name"],
                    store_url=STEAM_STORE_PAGE_BASE_URL + app["appid"],
                )
        print("done")
