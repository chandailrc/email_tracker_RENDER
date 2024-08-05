# Generated by Django 5.0.6 on 2024-08-01 12:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("receiving", "0001_initial"),
        ("sending", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="receivedemail",
            name="in_reply_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="replies",
                to="sending.sentemail",
            ),
        ),
    ]