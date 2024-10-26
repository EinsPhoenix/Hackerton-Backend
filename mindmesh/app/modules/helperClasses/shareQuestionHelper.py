# Standardbibliotheken
import logging

# Django-Bibliotheken
from django.shortcuts import get_object_or_404
from django.utils import timezone

# Drittanbieter-Bibliotheken
from ninja.errors import HttpError

# Lokale Module
from ...models import (
    Thread,
    SharedQuestion,
)

from ...schema import (
    CreateSharedQuestionSchema,
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