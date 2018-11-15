from django.db import models

class Movie(models.Model):
    title = models.TextField(null=True)
    overview = models.TextField(null=True)
    poster = models.TextField(null=True)
    runtime = models.IntegerField(null=True)
    vote_average = models.FloatField(null=True)
    release_date = models.DateTimeField(null=True)
    keywords = models.TextField(null=True)
    genres = models.TextField(null=True)
    production_companies = models.TextField(null=True)
    cast = models.TextField(null=True)
    directors = models.TextField(null=True)
    soup = models.TextField(null=True)
