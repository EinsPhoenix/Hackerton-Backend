from django.contrib.auth.models import AbstractUser, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
from .modules.AiModule import GenerateResponse
from django.utils import timezone

# Create your models here.

class CompanyProfile(models.Model):
    name = models.TextField()
    interests = models.TextField()
    branche = models.TextField()

class UserPreferences(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    preference = models.CharField(max_length=255)
    weight = models.FloatField()

    def __str__(self):
        return f"{self.user.username}'s preference"
    
class UploadedImage(models.Model):
    image_id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to='images/')  
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE) 

    def __str__(self):
        return self.image.name
    
class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True) 

    def __str__(self):
        return self.name


