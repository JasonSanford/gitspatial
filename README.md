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

## Testing

Use one command to test all apps

    python manage.py test gitspatial user api