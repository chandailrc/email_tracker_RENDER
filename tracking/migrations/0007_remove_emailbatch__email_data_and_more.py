# Generated by Django 4.1.13 on 2024-06-26 08:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracking", "0006_emailbatch__email_data"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="emailbatch",
            name="_email_data",
        ),
        migrations.RemoveField(
            model_name="emailbatch",
            name="created_at",
        ),
        migrations.RemoveField(
            model_name="emailbatch",
            name="emails",
        ),
        migrations.RemoveField(
            model_name="emailbatch",
            name="updated_at",
        ),
        migrations.AddField(
            model_name="emailbatch",
            name="body",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="emailbatch",
            name="last_sent",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emailbatch",
            name="recipients",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="emailbatch",
            name="subject",
            field=models.CharField(default="", max_length=200),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="batch_size",
            field=models.IntegerField(default=10),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="day_of_month",
            field=models.IntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(31),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="day_of_week",
            field=models.IntegerField(
                blank=True,
                choices=[
                    (0, "Monday"),
                    (1, "Tuesday"),
                    (2, "Wednesday"),
                    (3, "Thursday"),
                    (4, "Friday"),
                    (5, "Saturday"),
                    (6, "Sunday"),
                ],
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="delay_between_batches",
            field=models.IntegerField(default=300),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="delay_between_emails",
            field=models.IntegerField(default=30),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="schedule_type",
            field=models.CharField(
                choices=[
                    ("daily", "Daily"),
                    ("weekly", "Weekly"),
                    ("monthly", "Monthly"),
                ],
                default="daily",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="emailbatch",
            name="send_time",
            field=models.TimeField(default="12:00:00"),
        ),
    ]
