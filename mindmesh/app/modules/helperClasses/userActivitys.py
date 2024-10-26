# Standardbibliotheken
import json
import logging
import os
import time
import requests

# Django-Bibliotheken
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

# Google Auth-Bibliotheken
from google.auth.transport import requests
from google.oauth2 import id_token

# Drittanbieter-Bibliotheken
from ninja import NinjaAPI,Header
from ninja.errors import HttpError
from typing import List
from fastapi import HTTPException


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
    Job

)
from ..aiModule import GenerateResponse
from .textByPrefs import TextsByPrefs
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
    UserSchema
)

import datetime
import jwt
import random
import string

def get_user_from_token(authorization: str):
    try:
        token_user = extract_token(authorization)
        token = UserProfile.objects.get(token=token_user)  # Correct usage
        return token.user
    except UserProfile.DoesNotExist:
        return None

def extract_token(authorization: str = Header(None)) -> str:
    """Extrahiert den Bearer-Token aus dem Authorization-Header."""
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token not provided or invalid.")
    return authorization.split(" ")[1]

def create_custom_token(user_id, username, email):
    secret_key = os.getenv("SECRET_API_USERENCRYPTION")

    iat = datetime.datetime.now(datetime.timezone.utc)


    random_factor = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "iat": iat,
        "random_factor": random_factor
    }

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token


def perform_search(search_term, filters, request):
    search_results = {
        "threadsmatching": [],
        "commentsmatching": [],
        "sharedQuestions": [],
        "users": [],
        "jobs": []
    }

    # Search for users
    if filters.get('user', False):
        search_results["users"] = [user.username for user in User.objects.filter(username__icontains=search_term)]

    # Search for threads
    if filters.get('threads', False):
        threads = Thread.objects.filter(
            Q(titel__icontains=search_term) |
            Q(content__icontains=search_term) |
            Q(content_summary__icontains=search_term) |
            Q(main_tag__name__icontains=search_term) |
            Q(subtags__name__icontains=search_term) |
            Q(created_by__username__icontains=search_term)
        ).order_by('-created_at')

        unique_threads = {thread.id_thread: {
            "id_thread": thread.id_thread,
            "titel": thread.titel,
            "content": thread.content,
            "content_summary": thread.content_summary,
            "created_at": thread.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "created_by": thread.created_by.username,
            "main_tag": thread.main_tag.name if thread.main_tag else None,
            "sub_tags": [tag.name for tag in thread.subtags.all()],
            "upvotes": thread.upvotes,
            "image_url": request.build_absolute_uri(thread.image_url.image.url)
        } for thread in threads}

        search_results["threadsmatching"] = list(unique_threads.values())

    # Search for comments
    if filters.get('comments', False):
        comments = Comment.objects.filter(
            Q(content__icontains=search_term)
        ).order_by('-created_at')

        unique_comments = {comment.comment_id: {
            "comment_id": comment.comment_id,
            "content": comment.content,
            "created_at": comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "created_by": comment.created_by.username
        } for comment in comments}

        search_results["commentsmatching"] = list(unique_comments.values())

    # Search for tags
    if filters.get('tags', False):
        tags = Tag.objects.filter(name__icontains=search_term)
        search_results["tags"] = [tag.name for tag in tags]

    # Search for jobs
    if filters.get('jobs', False):
        jobs = Job.objects.filter(name__icontains=search_term)
        search_results["jobs"] = [{
            "name": job.name,
            "important_information": [
                {
                    "information": info.information,
                    "created_at": info.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                for info in job.ImportantInformations.all().order_by('-created_at')[:30]
            ]
        } for job in jobs]

    return search_results