# Generated by Django 3.2.14 on 2024-10-27 13:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_track_who_added_a_game_to_an_event'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='game',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.game'),
        ),
    ]
