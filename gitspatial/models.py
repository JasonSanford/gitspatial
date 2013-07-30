from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db import models as geo_models

from .behaviors import Timestampable


class Repo(Timestampable, models.Model):
    github_id = models.IntegerField()
    user = models.ForeignKey(User)
    name = models.CharField(max_length=1000)
    full_name = models.CharField(max_length=1000)
    github_private = models.BooleanField()
    synced = models.BooleanField(default=False)

    @property
    def hook_url(self):
        return 'http://gitspatial.com/api/v1/hooks/{0}'.format(self.id)

    def __unicode__(self):
        return self.full_name


class FeatureSet(Timestampable, models.Model):
    """
    Represents a GeoJSON file within a GitHub repo
    """
    repo = models.ForeignKey(Repo)
    file_name = models.CharField(max_length=1000)  # The filename in the repo, "fire-hydrants.geojson"
    name = models.CharField(max_length=255)  # The name without extension, "fire-hydrants"

    def __unicode__(self):
        return '{0}/{1}'.format(self.repo.full_name, self.name)


class Feature(geo_models.Model):
    """
    Represents a single feature belonging to a FeatureSet, a GeoJSON Feature
    """
    feature_set = models.ForeignKey(FeatureSet)
    geom = geo_models.GeometryField()
    properties = models.TextField()
    objects = geo_models.GeoManager()

    def __unicode__(self):
        return '<Feature {0} from {1}>'.format(self.id, self.feature_set)
