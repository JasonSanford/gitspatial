web: gunicorn gitspatial.wsgi --settings=gitspatial.settings.production
weblocal: gunicorn gitspatial.wsgi --settings=gitspatial.settings.development
celery: python manage.py celery worker -E -B --loglevel=WARNING
celerylocal: python manage.py celery worker -E -B --loglevel=DEBUG