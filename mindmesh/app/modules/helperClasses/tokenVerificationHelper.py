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

logger = logging.getLogger(__name__)

class TokenVerificationHelper:
    @staticmethod
    def verify_and_create_user(payload):
        try:
            device_type_to_env = {
                "android": "GOOGLE_CLIENT_ID_ANDROID",
                "ios": "GOOGLE_CLIENT_ID_IOS",
                "web": "GOOGLE_CLIENT_ID_WEB",
            }

            client_key = os.getenv(device_type_to_env.get(payload.devicetype))
            if client_key is None:
                raise ValueError("Invalid Device_Type or not found in environment variables")

            access_token = payload.token

            response = requests.get(f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}")
            logger.warning(f"0{response}")

            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Access Token is invalid")

            token_info = response.json()
            logger.warning(f"1{token_info}")

            profile_response = requests.get(
                f"https://people.googleapis.com/v1/people/me?personFields=names,emailAddresses",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            logger.warning(f": {profile_response}")

            if profile_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Unable to retrieve user profile")

            profile_info = profile_response.json()
            logger.warning(f"Profile Info: {profile_info}")

            name = profile_info.get('names', [{}])[0].get('displayName', 'User')
            email = profile_info.get('emailAddresses', [{}])[0].get('value', '')

            user, created = User.objects.get_or_create(
                username=name,
                email=email,
                defaults={'password': make_password(token_info['sub'])}
            )

            custom_token = create_custom_token(user.id, user.username, user.email)

            user_profile, _ = UserProfile.objects.get_or_create(user=user)
            user_profile.token = custom_token
            user_profile.save()

            preferences_list = []
            user_preferences = UserPreferences.objects.filter(user=user)
            if user_preferences.exists():
                preferences_list = [preference.preference for preference in user_preferences]

            return {
                "success": True,
                "token": custom_token,
                "created": created,
                "preferences": preferences_list
            }

        except Exception as e:
            logger.error(f"Error occurred while verifying token: {e}")
            return 404, {"success": False, "message": str(e)}