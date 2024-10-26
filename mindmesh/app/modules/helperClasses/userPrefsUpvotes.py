# Standardbibliotheken
import json
import logging
import os
import time

# Django-Bibliotheken
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

# Google Auth-Bibliotheken
from google.auth.transport import requests
from google.oauth2 import id_token

# Drittanbieter-Bibliotheken
from ninja import NinjaAPI
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
    UserSchema
)

def update_preferences(user_activity, thread, delta):
    main_tag = thread.main_tag
    
    try:
        preference = UserPreferences.objects.get(user=user_activity.user, preference=main_tag.name)
    except UserPreferences.DoesNotExist:
        print(main_tag.name)
        return

    if preference.weight < 100 and preference.weight > 0.05:
        preference.weight = min(100, preference.weight + delta)  
        preference.save()

    for subtag in thread.subtags.all():
        try:
            preference = UserPreferences.objects.get(user=user_activity.user, preference=subtag.name)
        except UserPreferences.DoesNotExist:
            return
        
        if preference.weight < 100 and preference.weight > 0.01:
            preference.weight = min(100, preference.weight + delta * 0.01)  
            preference.save()


def handle_thread_vote(user_activity, thread, upvote_type):
    if upvote_type == "upvote":
        if thread in user_activity.downvotedThreads.all():
            user_activity.downvotedThreads.remove(thread)
            user_activity.upvotedThreads.add(thread)
            thread.upvotes += 2
            update_preferences(user_activity, thread, 0.05)
        elif thread not in user_activity.upvotedThreads.all():
            user_activity.upvotedThreads.add(thread)
            thread.upvotes += 1
            update_preferences(user_activity, thread, 0.05)
        elif thread in user_activity.upvotedThreads.all():
            user_activity.upvotedThreads.remove(thread)
            thread.upvotes -= 1
            update_preferences(user_activity, thread, -0.05)
    elif upvote_type == "downvote":
        if thread in user_activity.upvotedThreads.all():
            user_activity.upvotedThreads.remove(thread)
            user_activity.downvotedThreads.add(thread)
            thread.upvotes -= 2
            update_preferences(user_activity, thread, -0.05)
        elif thread not in user_activity.downvotedThreads.all():
            user_activity.downvotedThreads.add(thread)
            thread.upvotes -= 1
            update_preferences(user_activity, thread, -0.05)
        elif thread in user_activity.downvotedThreads.all():
            user_activity.downvotedThreads.remove(thread)
            thread.upvotes += 1
            update_preferences(user_activity, thread, 0.05)

    thread.save()
    user_activity.save()


def handle_comment_vote(user_activity, comment, upvote_type):
    if upvote_type == "upvote":
        if comment in user_activity.downvotedComments.all():
            user_activity.downvotedComments.remove(comment)
            user_activity.upvotedComments.add(comment)
            comment.upvotes += 2
        elif comment not in user_activity.upvotedComments.all():
            user_activity.upvotedComments.add(comment)
            comment.upvotes += 1
        elif comment in user_activity.upvotedComments.all():
            user_activity.upvotedComments.remove(comment)
            comment.upvotes -= 1
    elif upvote_type == "downvote":
        if comment in user_activity.upvotedComments.all():
            user_activity.upvotedComments.remove(comment)
            user_activity.downvotedComments.add(comment)
            comment.upvotes -= 2
        elif comment not in user_activity.downvotedComments.all():
            user_activity.downvotedComments.add(comment)
            comment.upvotes -= 1
        elif comment in user_activity.downvotedComments.all():
            user_activity.downvotedComments.remove(comment)
            comment.upvotes += 1

    comment.save() 
    user_activity.save() 


def handle_shared_vote(user_activity, shared, upvote_type):
    if upvote_type == "upvote":
        if shared in user_activity.downvotedSharedQuestions.all():
            user_activity.downvotedSharedQuestions.remove(shared)
            user_activity.upvotedSharedQuestions.add(shared)
            shared.upvotes += 2
        elif shared not in user_activity.upvotedSharedQuestions.all():
            user_activity.upvotedSharedQuestions.add(shared)
            shared.upvotes += 1
        elif shared in user_activity.upvotedSharedQuestions.all():
            user_activity.upvotedSharedQuestions.remove(shared)
            shared.upvotes -= 1
    elif upvote_type == "downvote":
        if shared in user_activity.upvotedSharedQuestions.all():
            user_activity.upvotedSharedQuestions.remove(shared)
            user_activity.downvotedSharedQuestions.add(shared)
            shared.upvotes -= 2
        elif shared not in user_activity.downvotedSharedQuestions.all():
            user_activity.downvotedSharedQuestions.add(shared)
            shared.upvotes -= 1
        elif shared in user_activity.downvotedSharedQuestions.all():
            user_activity.downvotedSharedQuestions.remove(shared)
            shared.upvotes += 1

    shared.save()
    user_activity.save()