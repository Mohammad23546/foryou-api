#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt
pip install Pillow

# Run migrations
python manage.py makemigrations
python manage.py migrate

# جمع الملفات الثابتة (إذا كنت تستخدمها)
python manage.py collectstatic --no-input 