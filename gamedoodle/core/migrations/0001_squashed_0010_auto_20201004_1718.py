# Generated by Django 3.1.1 on 2020-10-04 15:52

import datetime
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("core", "0001_initial"),
        ("core", "0002_auto_20200927_1255"),
        ("core", "0003_event_uuid"),
        ("core", "0004_auto_20200927_1551"),
        ("core", "0005_auto_20201001_2133"),
        ("core", "0006_auto_20201004_1548"),
        ("core", "0007_game_image_url"),
        ("core", "0008_game_store_url"),
        ("core", "0009_auto_20201004_1631"),
        ("core", "0010_auto_20201004_1718"),
    ]

    initial = True
    atomic = False  # Fix initial migration for SQLite

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=256)),
                ("date", models.DateField(default=datetime.date.today)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SteamGame",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=256)),
                ("appid", models.PositiveIntegerField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Vote",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("username", models.CharField(max_length=256)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.event"
                    ),
                ),
                (
                    "game",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.steamgame"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="event",
            name="games",
            field=models.ManyToManyField(
                blank=True, default=None, null=True, to="core.SteamGame"
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AddConstraint(
            model_name="vote",
            constraint=models.UniqueConstraint(
                fields=("event", "game", "username"), name="unique vote"
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="games",
            field=models.ManyToManyField(blank=True, to="core.SteamGame"),
        ),
        migrations.RenameModel(
            old_name="SteamGame",
            new_name="Game",
        ),
        migrations.AlterField(
            model_name="game",
            name="appid",
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="game",
            name="image_url",
            field=models.CharField(blank=True, default="", max_length=256),
        ),
        migrations.AddField(
            model_name="game",
            name="store_url",
            field=models.CharField(blank=True, default="", max_length=256),
        ),
    ]
