# Generated by Django 3.1.1 on 2020-10-04 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_game_store_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='appid',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
    ]