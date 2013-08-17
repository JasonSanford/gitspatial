from django.db import models


class Timestampable(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Syncable(models.Model):
    NOT_SYNCED = 1
    SYNCING = 2
    SYNCED = 3
    ERROR_SYNCING = 4

    SYNC_CHOICES = (
        (NOT_SYNCED, 'Not Synced'),
        (SYNCING, 'Syncing'),
        (SYNCED, 'Synced'),
        (ERROR_SYNCING, 'Error Syncing'),
    )

    sync_status = models.IntegerField(choices=SYNC_CHOICES, default=NOT_SYNCED)

    class Meta:
        abstract = True
