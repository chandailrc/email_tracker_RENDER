# Generated by Django 5.0.6 on 2024-08-01 12:10

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("receiving", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Link",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("url", models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name="TrackingPixelToken",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("token", models.CharField(max_length=32, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="SentEmail",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("recipient", models.EmailField(max_length=254)),
                (
                    "cc",
                    models.TextField(
                        blank=True,
                        help_text="Comma-separated list of CC email addresses",
                    ),
                ),
                (
                    "bcc",
                    models.TextField(
                        blank=True,
                        help_text="Comma-separated list of BCC email addresses",
                    ),
                ),
                ("sender", models.EmailField(max_length=254)),
                ("subject", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("sent_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "message_id",
                    models.CharField(
                        blank=True, max_length=255, null=True, unique=True
                    ),
                ),
                ("thread_id", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "in_reply_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sent_replies",
                        to="receiving.receivedemail",
                    ),
                ),
            ],
        ),
    ]
