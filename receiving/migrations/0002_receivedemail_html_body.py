# Generated by Django 5.0.6 on 2024-07-23 07:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("receiving", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="receivedemail",
            name="html_body",
            field=models.TextField(blank=True, null=True),
        ),
    ]