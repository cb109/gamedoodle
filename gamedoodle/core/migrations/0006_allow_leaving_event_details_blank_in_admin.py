# Generated by Django 3.1.1 on 2020-11-24 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_event_details'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='details',
            field=models.TextField(blank=True, default=''),
        ),
    ]