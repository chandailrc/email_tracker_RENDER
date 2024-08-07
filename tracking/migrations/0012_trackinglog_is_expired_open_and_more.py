# Generated by Django 4.1.13 on 2024-07-02 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracking", "0011_trackingpixeltoken"),
    ]

    operations = [
        migrations.AddField(
            model_name="trackinglog",
            name="is_expired_open",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="trackinglog",
            name="tracking_type",
            field=models.CharField(default="default", max_length=255),
        ),
    ]
