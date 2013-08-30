# GitSpatial

A spatial API for your GitHub-hosted GeoJSON.

## Overview

GitHub now supports [rendering GeoJSON files](https://help.github.com/articles/mapping-geojson-files-on-github). This makes it easy to collaborate on geo data. GitSpatial provides a spatial API for GeoJSON hosted at GitHub. 

## How it Works

1. Visit http://gitspatial.herokuapp.com
2. Authorize the site to access your GitHub repos
3. Sync the repos that have GeoJSON in them
4. Sync individual GeoJSON files within these repos
5. Utilize the API to query your features

### Search by Bounding Box

Find all parks within a map view:

    http://gitspatial.herokuapp.com/api/v1/JasonSanford/mecklenburg-gis-opendata/parks?bbox=-81.025,35.023,-80.685,35.487

### Search by Point and Radius

Find all parks within 3000 meters of a point:

    http://gitspatial.herokuapp.com/api/v1/JasonSanford/mecklenburg-gis-opendata/parks?lat=35.255&lon=-80.855&distance=3000

## Development

GitSpatial is a Django app that uses PostGIS as a backend to GeoDjango. So, you might run into trouble getting dependencies installed.

### Non-Python dependencies

* GEOS
* GDAL
* Proj

### Virtual Environment

Create a virtual environment. Python 2.7 is ideal as this is what Heroku uses. I drop the virtual envrionment within the root of the project. The `venv` directory is in `.gitignore`.

    virtualenv venv

Source to the virtual environment.

    source venv/bin/activate

Install dependencies defined in `requirements.txt`.

    pip install -r requirements.txt

### Envrionment Variables

To keep secret keys, passwords and such out of version control, we store them in environment variables. Below are the variables required to run.

    AWS_ACCESS_KEY_ID=my-aws-key
    AWS_SECRET_ACCESS_KEY=super-secret-aws-secret-access-key
    DATABASE_URL=postgis://user:password@host:port/db_name
    GITHUB_APP_ID=not-a-secret
    GITHUB_API_SECRET=super-secret
    LD_LIBRARY_PATH=/app/.heroku/vendor/lib:vendor/geos/geos/lib:vendor/proj/proj/lib:vendor/gdal/gdal/lib
    LIBRARY_PATH=/app/.heroku/vendor/lib:vendor/geos/geos/lib:vendor/proj/proj/lib:vendor/gdal/gdal/lib

### Database Stuff

Assuming you have a database already created and credentials are in the `DATABASE_URL` envrionment variable, we just need to `syncdb` to get the necessary tables created. Do not create a superuser if prompted.

    python manage.py syncdb

### Running the App

The django web server (gunicorn) and the celery process are defined in `Procfile` and `Procfile-dev` and point to production and development settings respectively. Run with `Foreman`. Heroku will look for `Procfile`, while we'll use `Procfile-dev` locally.

    foreman start -f Procfile-dev

## Deployment

### Web App

The application is currently hosted at heroku. Deployments are handled by `git push`'ing to a heroku endpoint. The current git remote is `git@heroku.com:gitspatial.git`

Add this remote to enable pushing.

    git remote add heroku git@heroku.com:gitspatial.git

Then, deploying the latest code is just `git push heroku master`.

A [custom buildpack](https://github.com/JasonSanford/heroku-buildpack-python-geos) is used to include the GEOS, GDAL and Proj binaries necessary for Shapely and GeoDjango. To force deployment to use a custom buildpack, add the following heroku config.

    heroku config:set BUILDPACK_URL=git://github.com/JasonSanford/heroku-buildpack-python-geos.git

Additionally, the `LIBRARY_PATH` and `LD_LIBRARY_PATH` enverionment variables must be updated so that Shapely can locate the necessary binaries.

    heroku config:set LIBRARY_PATH=/app/.heroku/vendor/lib:vendor/geos/geos/lib:vendor/proj/proj/lib:vendor/gdal/gdal/lib
    heroku config:set LD_LIBRARY_PATH=/app/.heroku/vendor/lib:vendor/geos/geos/lib:vendor/proj/proj/lib:vendor/gdal/gdal/lib

### Static Files

Static file deployment is handled by the `collectstatic` method when pushing to Heroku. We're using a combination of django-store and boto to automatically collect/push static files to Amazon S3 during deployment.

All static files should be placed in the `/static` directory if they need to be deployed.

**Note!** - With the custom buildpack, collectstatic doesn't seem to be running automatically. To run manually:

    heroku run python manage.py collectstatic

## Testing

Use one command to test all apps

    python manage.py test gitspatial api user geojson
