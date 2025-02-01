#!/usr/bin/env bash
# exit on error
set -o errexit

# تثبيت المتطلبات
pip install -r requirements.txt

# تطبيق الترحيلات
python manage.py migrate

# جمع الملفات الثابتة (إذا كنت تستخدمها)
python manage.py collectstatic --no-input 