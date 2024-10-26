# Standardbibliotheken
import json
import logging
import os
import time
import hashlib
from datetime import date

# Django-Bibliotheken
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from django.core.files.images import get_image_dimensions
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files.storage import default_storage

# Google Auth-Bibliotheken
from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Drittanbieter-Bibliotheken
from ninja import NinjaAPI,Schema, UploadedFile, Form, File, Header
from ninja.errors import HttpError
from typing import List
from fastapi import HTTPException
from django.db.models import Q


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
    SearchRequests,
    UploadedImage

)

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
    SearchRequest,
    ReportPayload,
    PublicUserResponse,
    UserRequest,
    ImageResponseSchema,
    ImagePayload,
    SearchResponseSchema,
    CommentResponseSchema,
    CommentCreateSchema,
    MessageResponseSchema,
    GoogleVerificationSchema

)

logger = logging.getLogger(__name__)

class ThreadHelper():
    
    @staticmethod
    def format_thread_response(thread, request):
        return ThreadResponseSchema(
            success=True,
            id_thread=thread.id_thread,
            titel=thread.titel,
            content=thread.content,
            content_summary=thread.content_summary,
            main_tag=thread.main_tag.name,
            subtags=[tag.name for tag in thread.subtags.all()],
            created_at=thread.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            upvotes=thread.upvotes,
            image_url=request.build_absolute_uri(thread.image_url.image.url),
            created_by=thread.created_by.username
        )

    @staticmethod
    def handle_image_upload(file, user):
        if file:
            try:
                width, height = get_image_dimensions(file)
                if width and height:
                    image_instance = UploadedImage(image=file, uploaded_by=user, uploaded_at=timezone.now())
                    image_instance.save()
                    image_url = default_storage.url(image_instance.image.name)
                    return image_instance, image_url
                else:
                    raise ValueError("Invalid image dimensions")
            except Exception as e:
                logger.error(f"Error occurred while uploading the image: {e}")
                raise e
        return None, None
    
    @staticmethod
    def delete_existing_image(thread):
        if thread.image_url:
            try:
                image_instance = get_object_or_404(UploadedImage, id=thread.image_url.id)
                image_instance.image.delete()
                image_instance.delete()
            except Exception as e:
                raise Exception("Error deleting existing image")

    @staticmethod
    def create_thread(payload, user, main_tag, image_instance=None):
        new_thread = Thread.objects.create(
            titel=payload.titel,
            content=payload.content,
            content_summary=payload.content_summary or "",
            main_tag=main_tag,
            created_by=user,
            created_at=timezone.now(),
            upvotes=0,
            image_url=image_instance  
        )

        if payload.subtags:
            new_thread.subtags.set(Tag.objects.filter(name__in=payload.subtags))
        
        return new_thread
    
    @staticmethod
    def update_thread_fields(thread, payload, main_tag=None):
        try:
            thread.titel = payload.titel or thread.titel
            thread.content = payload.content or thread.content
            thread.content_summary = payload.content_summary or thread.content_summary
            if main_tag:
                thread.main_tag = main_tag
            if payload.subtags:
                subtags_to_add = Tag.objects.filter(name__in=payload.subtags)
                thread.subtags.set(subtags_to_add)
        except Exception as e:
            raise Exception("Error updating thread fields")
        
    @staticmethod
    def get_thread_by_id(thread_id: int):
        try:
            return get_object_or_404(Thread, id_thread=thread_id)
        except Exception as e:
            logger.error(f"Error occurred while fetching thread: {e}")
            raise HttpError(404, "Thread not found")