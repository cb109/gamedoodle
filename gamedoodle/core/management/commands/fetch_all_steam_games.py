from django.conf import settings
from django.core.management.base import BaseCommand

import requests
from gamedoodle.core.models import Game


class Command(BaseCommand):
    def handle(self, *args, **options):
        response = requests.get(settings.STEAM_API_URL_GET_APP_LIST)
        data = response.json()
        apps = data["applist"]["apps"]

        fixed_name = app["name"]

        if Game.objects.count() == 0:
            games = [Game(appid=app["appid"], name=fixed_name) for app in apps]
            Game.objects.bulk_create(games)
        else:
            for i, app in enumerate(apps):
                print(i + 1, len(apps))
                Game.objects.get_or_create(
                    appid=app["appid"],
                    name=fixed_name,
                    store_url=settings.STEAM_STORE_PAGE_BASE_URL + app["appid"],
                )
        print("done")
