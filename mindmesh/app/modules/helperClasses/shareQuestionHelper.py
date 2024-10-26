# Standardbibliotheken
import json
import logging
import os
import time
import hashlib
from datetime import date
import requests

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
from ninja import NinjaAPI, Schema, UploadedFile, Form, File, Header
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
    UploadedImage,
    ImportantInformation,
    Job,
)
from ..aiModule import GenerateResponse
from ..helperClasses.threadsHelper import ThreadHelper
from ..helperClasses.textByPrefs import TextsByPrefs

from ..helperClasses.tokenVerificationHelper import TokenVerificationHelper
from ..helperClasses.userActivitys import (
    get_user_from_token,
    create_custom_token,
    perform_search,
)
from ..helperClasses.report import ReportReciever
from ..helperClasses.userPrefsUpvotes import (
    handle_thread_vote,
    handle_comment_vote,
    handle_shared_vote,
)
from ..helperClasses.userProfileLogin import (
    handle_existing_user,
    create_new_user,
)
from ...schema import (
    NotFoundSchema,
    CreateThreadSchema,
    CreateUserSchema,
    ThreadResponseSchema,
    CheckQuestionSchema,
    TagGivingSchema,
    UserPrefsResponse,
    UpvoteTypeResponse,
    SharedQuestionResponseSchema,
    CreateSharedQuestionSchema,
    PasswordConfirmationSchema,
    SearchRequest,
    ReportPayload,
    PublicUserResponse,
    UserRequest,
    ImageResponseSchema,
    ImagePayload,
    SearchResponseSchema,
    CommentResponseSchema,
    CommentCreateSchema,
    GoogleVerificationSchema,
    ImportandResponseSchema,
)

logger = logging.getLogger(__name__)


class ShareQuestionHelper():
    @staticmethod
    def create_shared_question(user, payload: CreateSharedQuestionSchema):
        if user is None:
            raise HttpError(404, "User not found")
        
        thread = get_object_or_404(Thread, id_thread=payload.thread_id)

        new_shared_question = SharedQuestion.objects.create(
            thread=thread,
            content=payload.content,
            created_by=user,
            created_at=timezone.now(),
            upvotes=0
        )

        response_data = {
            "success": True,
            "shared_id": new_shared_question.shared_id,
            "thread_id": new_shared_question.thread.id_thread,
            "content": new_shared_question.content,
            "created_at": new_shared_question.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "created_by": new_shared_question.created_by.username,
            "upvotes": new_shared_question.upvotes
        }

        return response_data

    @staticmethod
    def get_shared_questions_by_user(user):
        if user is None:
            raise HttpError(404, "User not found")
        
        shared_questions = SharedQuestion.objects.filter(created_by=user).order_by('-upvotes')

        response_data = [
            {
                "success": True,
                "shared_id": shared_question.shared_id,
                "thread_id": shared_question.thread.id_thread,
                "content": shared_question.content,
                "created_at": shared_question.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": shared_question.created_by.username,
                "upvotes": shared_question.upvotes
            }
            for shared_question in shared_questions
        ]

        return response_data

    @staticmethod
    def get_shared_questions_by_thread(thread_id: int):
        thread = get_object_or_404(Thread, id_thread=thread_id)

        shared_questions = SharedQuestion.objects.filter(thread=thread)

        response_data = [
            {
                "success": True,
                "shared_id": shared_question.shared_id,
                "thread_id": shared_question.thread.id_thread,
                "content": shared_question.content,
                "created_at": shared_question.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": shared_question.created_by.username,
                "upvotes": shared_question.upvotes
            }
            for shared_question in shared_questions
        ]

        return response_data

    @staticmethod
    def delete_shared_question(user, question_id: int):
        if user is None:
            raise HttpError(404, "User not found")
        
        shared_question = get_object_or_404(SharedQuestion, shared_id=question_id, created_by=user)
        shared_question.delete()

        return None