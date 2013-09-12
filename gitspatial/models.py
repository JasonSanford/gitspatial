from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db import models as geo_models

from .behaviors import Syncable, Timestampable
from .utils import disk_size_format


class Repo(Syncable, Timestampable, models.Model):
    github_id = models.IntegerField()
    user = models.ForeignKey(User)
    name = models.CharField(max_length=1000)
    full_name = models.CharField(max_length=1000)
    github_private = models.BooleanField()
    master_branch = models.CharField(max_length=200)
    synced = models.BooleanField(default=False)

    @property
    def hook_url(self):
        return 'http://gitspatial.com/api/v1/hooks/{0}'.format(self.id)

    def __unicode__(self):
        return self.full_name


class FeatureSet(Syncable, Timestampable, models.Model):
    """
    Represents a GeoJSON file within a GitHub repo
    """
    repo = models.ForeignKey(Repo)
    path = models.CharField(max_length=1000)  # The path for a file in the repo, "fire-hydrants.geojson", "data/geojson/pump-stations.geojson"
    name = models.CharField(max_length=1000)  # The editable name of the feature set, initially the same as path
    size = models.IntegerField()  # Size in bytes, just trusting GitHub API here
    synced = models.BooleanField(default=False)  # Just like Repo, not all are synced

    unique_together = ('repo', 'name')

    @property
    def bounds(self):
        # A (minx, miny, maxx, maxy) tuple representing the bounding box of the feature set
        if hasattr(self, '_bounds'):
            return self._bounds
        else:
            bounds = Feature.objects.filter(feature_set=self).extent()
            self._bounds = bounds
        return self._bounds

    @property
    def center(self):
        # A (lng, lat) tuple containing the approximage center of the feature set
        xmin, ymin, xmax, ymax = self.bounds
        x = (xmin + xmax) / 2
        y = (ymin + ymax) / 2
        return (x, y)

    @property
    def size_pretty(self):
        return disk_size_format(self.size)

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

    ordering = ['id']

    def __unicode__(self):
        return '<Feature {0} from {1}>'.format(self.id, self.feature_set)
