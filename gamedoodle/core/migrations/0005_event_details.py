# Generated by Django 3.1.1 on 2020-11-24 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_make_event_date_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='details',
            field=models.TextField(default=''),
        ),
    ]
