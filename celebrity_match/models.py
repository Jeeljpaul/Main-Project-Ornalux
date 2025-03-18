from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
from django.db import models

class Jewelry(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="jewelry_store/")
    category = models.CharField(max_length=50, choices=[
        ("Ring", "Ring"),
        ("Earring", "Earring"),
        ("Necklace", "Necklace"),
        ("Bracelet", "Bracelet")
    ])
    features = models.TextField()  # Store feature embeddings

    def __str__(self):
        return self.name

class CelebrityUpload(models.Model):
    image = models.ImageField(upload_to="celebrity_uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Upload {self.id} at {self.uploaded_at}"
