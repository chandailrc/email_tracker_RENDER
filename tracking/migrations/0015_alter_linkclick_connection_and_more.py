# Generated by Django 5.0.6 on 2024-07-17 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracking", "0014_email_sender"),
    ]

    operations = [
        migrations.AlterField(
            model_name="linkclick",
            name="connection",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="linkclick",
            name="device_type",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="linkclick",
            name="language",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="linkclick",
            name="method",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="linkclick",
            name="protocol",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="linkclick",
            name="screen_resolution",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="trackinglog",
            name="connection",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="trackinglog",
            name="device_type",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="trackinglog",
            name="language",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="trackinglog",
            name="method",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="trackinglog",
            name="protocol",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="trackinglog",
            name="screen_resolution",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
