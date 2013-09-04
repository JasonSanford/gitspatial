web: gunicorn gitspatial.wsgi --settings=gitspatial.settings.development -b 0.0.0.0:8000
celery: python manage.py celery worker -E -B --loglevel=DEBUG