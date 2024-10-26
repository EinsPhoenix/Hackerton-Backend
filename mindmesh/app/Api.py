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


# # Lokale Module
# from .models import (
# )
# from .modules.AiModule import GenerateResponse
# from .modules.HelperClasses.ThreadsHelper import ThreadHelper
# from .modules.HelperClasses.TextsByPrefs import TextsByPrefs
# from .modules.HelperClasses.ShareQuestionHelper import ShareQuestionHelper
# from .modules.HelperClasses.TokenVerificationHelper import TokenVerificationHelper
# from .modules.HelperClasses.UserActivitys import (
#     get_user_from_token,
#     create_custom_token,
#     perform_search,
# )
# from .modules.HelperClasses.Report import ReportReciever
# from .modules.HelperClasses.UserPrefsUpvotes import (
#     handle_thread_vote,
#     handle_comment_vote,
#     handle_shared_vote,
# )
# from .modules.HelperClasses.UserProfileLogin import (
#     handle_existing_user,
#     create_new_user,
# )
# from .schema import (
 
# )

# Initialisierung der API
api = NinjaAPI()

# Initialisierung logger
logger = logging.getLogger(__name__)


@api.get("/Texts", response={201: List[ThreadResponseSchema], 404: NotFoundSchema})
def get_texts(request, authorization: str = Header(None)):
    try:
        user = get_user_from_token()
        if user == None:
            return 404, {"success": False, "message": "User not found"}
        user_pref_getter = TextsByPrefs(user)
        print(1)
        threads = user_pref_getter.get_weighted_threads(30)
        print(2)

        return 201, [
            ThreadHelper.format_thread_response(thread, request) for thread in threads
        ]

    except Exception as e:
        logger.error(f"Error occurred while fetching threads: {e}")
        return 404, {"success": False, "message": str(e)}


