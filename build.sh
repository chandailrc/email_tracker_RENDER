#!/usr/bin/env bash
# Exit on error
set -o errexit

# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Reset database. Uncomment only if needed
python manage.py reset_db

# Apply any outstanding database migrations
python manage.py migrate
