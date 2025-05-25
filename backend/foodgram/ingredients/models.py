from django.db import models


class Ingredient(models.Model):
    name = models.CharField(unique=True, max_length=200)
    measurement_unit = models.CharField(max_length=50)
    class Meta:
        
