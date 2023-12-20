import os

from django.db import models


class Picture(models.Model):
    checksum = models.CharField(max_length=32, unique=True)
    path = models.CharField(max_length=2000)
    small_path = models.CharField(max_length=2000)
    date = models.DateTimeField()
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)

    def __str__(self):
        return os.path.basename(self.path)

# class Album(models.Model):