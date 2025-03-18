from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
from django.db import models

class Jewelry(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='jewelry_images/')  # Store jewelry images

    def __str__(self):
        return self.name
