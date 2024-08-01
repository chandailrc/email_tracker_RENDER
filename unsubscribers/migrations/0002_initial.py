# Generated by Django 5.0.6 on 2024-08-01 12:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("unsubscribers", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="unsubscribeduser",
            name="unsubscribed_from",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="unsubscribed_users",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
