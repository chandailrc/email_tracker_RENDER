import os
import shutil
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings

class Command(BaseCommand):
    help = 'Drop all tables, delete migrations, and reset the database'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            self.drop_all_tables()
        self.stdout.write(self.style.SUCCESS('Successfully dropped all tables.'))

        self.delete_migrations()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all migrations.'))

        self.make_migrations()
        self.stdout.write(self.style.SUCCESS('Successfully created new migrations.'))

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

    def delete_migrations(self):
        for app in settings.INSTALLED_APPS:
            if '.' not in app:  # Ignore django built-in apps
                migrations_dir = os.path.join(settings.BASE_DIR, app, 'migrations')
                if os.path.exists(migrations_dir):
                    for filename in os.listdir(migrations_dir):
                        file_path = os.path.join(migrations_dir, filename)
                        if filename != '__init__.py':
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)

    def make_migrations(self):
        from django.core.management import call_command
        call_command('makemigrations')

    def run_migrations(self):
        from django.core.management import call_command
        call_command('migrate')