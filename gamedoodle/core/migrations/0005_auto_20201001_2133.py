# Generated by Django 3.1.1 on 2020-10-01 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20200927_1551'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='games',
            field=models.ManyToManyField(blank=True, to='core.SteamGame'),
        ),
    ]
