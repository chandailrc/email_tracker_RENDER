from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction
from django.apps import apps

class Command(BaseCommand):
    help = 'Drop all tables and reset the database'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            self.drop_all_tables()
        self.stdout.write(self.style.SUCCESS('Successfully dropped all tables.'))
        
        self.run_migrations()
        self.stdout.write(self.style.SUCCESS('Successfully ran all migrations.'))

    def drop_all_tables(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema='public'
            """)
            tables = cursor.fetchall()
            for table in tables:
                cursor.execute(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE')

    def run_migrations(self):
        from django.core.management import call_command
        call_command('migrate')

