web: gunicorn gitspatial.wsgi --settings=gitspatial.settings.production --log-level INFO
celery: python manage.py celery worker -E -B --loglevel=INFO