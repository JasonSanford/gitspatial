# GitSpatial

A spatial API for your GitHub-hosted GeoJSON.

Read more in a [blog post](http://geojason.info/2013/gitspatial-a-spatial-api-for-your-github-hosted-geojson/) or [see it in action](http://gitspatial.com/).

## Overview

GitHub now supports [rendering GeoJSON files](https://help.github.com/articles/mapping-geojson-files-on-github). This makes it easy to collaborate on geo data. GitSpatial provides a spatial API for GeoJSON hosted at GitHub. 

## How it Works

1. Visit http://gitspatial.com
2. Authorize the site to access your GitHub repos
3. Sync the repos that have GeoJSON in them
4. Sync individual GeoJSON files within these repos
5. We add a post-receive hook to your GitHub repo so we get notified when you might have updated features
6. Utilize the API to query your features

<img src="http://s3.amazonaws.com/geojason/img/gitspatial-demo.gif" />

### Search by Bounding Box

Find all parks within a map view:

    http://gitspatial.com/api/v1/JasonSanford/mecklenburg-gis-opendata/parks?bbox=-81.025,35.023,-80.685,35.487

### Search by Point and Radius

Find all parks within 3000 meters of a point:

    http://gitspatial.com/api/v1/JasonSanford/mecklenburg-gis-opendata/parks?lat=35.255&lon=-80.855&distance=3000

## Development

GitSpatial is a Django app that uses PostGIS as a backend to GeoDjango. So, you might run into trouble getting dependencies installed.

### Non-Python dependencies

* GEOS
* GDAL
* Proj

### Virtual Environment

Create a virtual environment. I drop the virtual envrionment within the root of the project. The `venv` directory is in `.gitignore`.

    virtualenv venv

Source to the virtual environment.

    source venv/bin/activate

Install dependencies defined in `requirements.txt`.

    pip install -r requirements.txt

### Environment Variables

To keep secret keys, passwords and such out of version control, we store them in environment variables. Below are the variables required to run.

    AWS_ACCESS_KEY_ID=my-aws-key
    AWS_SECRET_ACCESS_KEY=super-secret-aws-secret-access-key
    DATABASE_URL=postgis://user:password@host:port/db_name
    GITHUB_APP_ID=not-a-secret
    GITHUB_API_SECRET=super-secret

### Database Stuff

Assuming you have a database already created and credentials are in the `DATABASE_URL` envrionment variable, we just need to `syncdb` to get the necessary tables created. Do not create a superuser if prompted.

    python manage.py syncdb

### Running the App

The django web server (gunicorn) and the celery process are defined in `Procfile`. Run with `Foreman`.

    foreman start

### Static Files

Static file deployment is handled by the `collectstatic` command. We're using a combination of django-store and boto to automatically collect/push static files to Amazon S3 during deployment.

All static files should be placed in the `/static` directory if they need to be deployed.

    python manage.py collectstatic

## Testing

Do it with fab

    fab test

## Deploying

Do it with fab

    fab deploy

