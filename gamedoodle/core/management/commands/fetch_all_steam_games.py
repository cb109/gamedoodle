from typing import List

from django.conf import settings
from django.core.management.base import BaseCommand

import requests
from gamedoodle.core.models import Game


class Command(BaseCommand):
    def handle(self, *args, **options):
        apps: List[dict] = []
        url: str = settings.STEAM_API_URL_GET_APP_LIST

        data: dict = requests.get(url).json()
        last_appid: int = data["response"].get("last_appid", -1)
        apps += data["response"]["apps"]

        while data["response"].get("have_more_results", False) and last_appid:
            url = settings.STEAM_API_URL_GET_APP_LIST + f"&last_appid={last_appid}"
            data =  requests.get(url).json()
            last_appid = data["response"].get("last_appid", -1)
            apps += data["response"]["apps"]

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
