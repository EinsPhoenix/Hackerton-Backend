# Standardbibliotheken
import json
import logging
import os
import time
import hashlib

# Django-Bibliotheken
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from .UserActivitys import get_user_from_token,create_custom_token, perform_search

# Google Auth-Bibliotheken
from google.auth.transport import requests
from google.oauth2 import id_token

import os
import requests
from django.contrib.auth.hashers import make_password

# Drittanbieter-Bibliotheken
from ninja import NinjaAPI, UploadedFile
from ninja.errors import HttpError
from typing import List
from fastapi import HTTPException

from django.core.files.images import get_image_dimensions
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files.storage import default_storage

# Lokale Module
from ...models import (
    Thread,
    User,
    Tag,
    UserProfile,
    UserActivity,
    Comment,
    UserPreferences,
    SharedQuestion,
    ReportModel,
    UploadedImage
)
from ..AiModule import GenerateResponse
from .TextsByPrefs import TextsByPrefs
from ...schema import (
    NotFoundSchema,
    CreateThreadSchema,
    UpdateThreadSchema,
    CreateUserSchema,
    ThreadResponseSchema,
    CheckQuestionSchema,
    TagGivingSchema,
    UserPrefsResponse,
    UpvoteTypeResponse,
    SharedQuestionResponseSchema,
    CreateSharedQuestionSchema,
    PasswordConfirmationSchema,
    UserSchema,
    ReportPayload
)

logger = logging.getLogger(__name__)
def handle_existing_user(user: User, file: UploadedFile):
    
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    custom_token = create_custom_token(user.id,user.username,user.email)
    user_profile.token = custom_token
    user_profile.save()

    if file:
        return process_user_image(file, user, user_profile)
    
    set_default_image(user_profile)
    user_profile.save()
    
    preferences_list = []
    user_preferences = UserPreferences.objects.filter(user=user_profile.user)
    if user_preferences.exists():
        preferences_list = [preference.preference for preference in user_preferences]
            
    
    return {
        "success": True,
        "token": user_profile.token,
        "created": False,
        "preferences": preferences_list
    }


def create_new_user(payload, file: UploadedFile):
    new_user = User(
        username=payload.username,
        email=payload.email,
        password=make_password(payload.password),
    )
    new_user.save()

    custom_token = create_custom_token(new_user.id,new_user.username,new_user.email)
    user_profile = UserProfile.objects.create(user=new_user, token=custom_token)

    if file:
        return process_user_image(file, new_user, user_profile)
    
    set_default_image(user_profile)
    user_profile.save()
    
    preferences_list = []
    user_preferences = UserPreferences.objects.filter(user=user_profile.user)
    if user_preferences.exists():
        preferences_list = [preference.preference for preference in user_preferences]
            
    return {"success": True, "token": user_profile.token, "created": True, "preferences": preferences_list}

def process_user_image(file: UploadedFile, user: User, user_profile: UserProfile):
    existing_image_instance = user_profile.image_url 

  
    if existing_image_instance:
        if check_image_metadata(file, existing_image_instance):  
            preferences_list = []
            user_preferences = UserPreferences.objects.filter(user=user_profile.user)
            if user_preferences.exists():
                preferences_list = [preference.preference for preference in user_preferences]
            
            return {"success": True, "token": user_profile.token, "created": False, "preferences": preferences_list}
        else:
          
            existing_image_instance.delete()


    new_image_instance = handle_uploaded_file(file, user)
    
    if new_image_instance:  
        user_profile.image_url = new_image_instance  
        user_profile.save()
        
        preferences_list = []
        user_preferences = UserPreferences.objects.filter(user=user_profile.user)
        if user_preferences.exists():
            preferences_list = [preference.preference for preference in user_preferences]
            
        return {"success": True, "token": user_profile.token, "created": True, "preferences": preferences_list}
    
    return {"success": False, "message": "Das Bild konnte nicht gespeichert werden."}



def set_default_image(user_profile: UserProfile):
    default_image = UploadedImage.objects.filter(image='images/images/images.jpeg').first()
    if default_image:
        user_profile.image_url = default_image

def hash_image(file):
    hasher = hashlib.md5()
    for chunk in iter(lambda: file.read(4096), b""):
        hasher.update(chunk)
    file.seek(0)
    return hasher.hexdigest()

def check_image_metadata(new_image_file, existing_image_instance):
    if existing_image_instance is None:
        return False

    existing_image_file = existing_image_instance.image  
    
    new_image_hash = hash_image(new_image_file)  
    existing_image_hash = hash_image(existing_image_file)  
    return new_image_hash == existing_image_hash  
  

def handle_uploaded_file(file: UploadedFile, user: User):
    try:
        logger.warning("Processing uploaded file")
        width, height = get_image_dimensions(file)
        if width and height:
            
            image_instance = UploadedImage(image=file, uploaded_by=user, uploaded_at=timezone.now())
            image_instance.save()
            return image_instance
        else:
            raise ValidationError("The uploaded file is not a valid image.")
    except ValidationError as e:
        raise HttpError(404, str(e))
    except Exception:
        raise HttpError(404, "Invalid image file.")