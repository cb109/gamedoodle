# Generated by Django 3.1.1 on 2020-10-04 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20201004_1548'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='image_url',
            field=models.CharField(default='', max_length=256),
        ),
    ]