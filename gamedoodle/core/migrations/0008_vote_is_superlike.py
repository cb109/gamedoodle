# Generated by Django 3.1.13 on 2021-11-23 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_event_listed"),
    ]

    operations = [
        migrations.AddField(
            model_name="vote",
            name="is_superlike",
            field=models.BooleanField(default=False),
        ),
    ]