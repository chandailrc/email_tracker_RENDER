# Generated by Django 5.0.6 on 2024-07-19 19:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tracking", "0016_alter_trackinglog_email_remove_link_email_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="UnsubscribedUser",
        ),
    ]