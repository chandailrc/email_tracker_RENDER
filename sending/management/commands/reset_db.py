# myapp/management/commands/reset_db.py
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection

class Command(BaseCommand):
    help = 'Delete all entries and reset primary key sequences'

    def handle(self, *args, **kwargs):
        self.delete_all_entries()
        self.reset_primary_key_sequence()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all entries and reset primary key sequences'))

    def delete_all_entries(self):
        for model in apps.get_models():
            model.objects.all().delete()

    def reset_primary_key_sequence(self):
        with connection.cursor() as cursor:
            for model in apps.get_models():
                table_name = model._meta.db_table
                primary_key_field = model._meta.pk.name
                sequence_name = f"{table_name}_{primary_key_field}_seq"
                try:
                    cursor.execute(f"SELECT 1 FROM pg_class WHERE relname='{sequence_name}';")
                    if cursor.fetchone():
                        cursor.execute(f"SELECT setval('{sequence_name}', 1, false);")
                    else:
                        self.stdout.write(self.style.WARNING(f"Sequence '{sequence_name}' does not exist."))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Could not reset sequence for table {table_name}: {e}"))
