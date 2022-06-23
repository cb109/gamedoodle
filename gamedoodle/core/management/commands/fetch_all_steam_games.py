from django.conf import settings
from django.core.management.base import BaseCommand

import requests
from gamedoodle.core.models import Game


class Command(BaseCommand):
    def handle(self, *args, **options):
        response = requests.get(settings.STEAM_API_URL_GET_APP_LIST)
        data = response.json()

        apps = data["applist"]["apps"]
        app_id_to_name = {app["appid"]: app["name"].strip() for app in apps}

        fetched_app_ids = [app["appid"] for app in apps]
        existing_app_ids = Game.objects.all().values_list("appid", flat=True)
        new_app_ids = set(fetched_app_ids) - set(existing_app_ids)

        games = [
            Game(appid=app_id, name=app_id_to_name[app_id]) for app_id in new_app_ids
        ]
        print(f"Fetched {len(games)} new games...")
        Game.objects.bulk_create(games)
        print("Done")
