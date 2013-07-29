from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db import models as geo_models

from .behaviors import Timestampable


class Repo(Timestampable, models.Model):
    github_id = models.IntegerField()
    user = models.ForeignKey(User)
    name = models.CharField(max_length=1000)
    full_name = models.CharField(max_length=1000)
    private = models.BooleanField()
    synced = models.BooleanField()

    def __unicode__(self):
        return self.full_name


class Feature(geo_models.Model):
    repo = models.ForeignKey(Repo)
    geom = geo_models.GeometryField()
    properties = models.TextField()
    objects = geo_models.GeoManager()

    def __unicode__(self):
        return '<Feature {0} from {1}>'.format(self.id, self.repo.full_name)
