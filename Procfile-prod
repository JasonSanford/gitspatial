web: gunicorn gitspatial.wsgi --settings=gitspatial.settings.production
celery: python manage.py celery worker -E -B --loglevel=INFO