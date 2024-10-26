# Standardbibliotheken
import json
import logging
from datetime import date
from typing import List, Optional

# Django-Bibliotheken
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
# Drittanbieter-Bibliotheken
from ninja import NinjaAPI, Schema, UploadedFile, Form, File, Header
from ninja.errors import HttpError

# Lokale Module
from .models import (
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
    QuizAbsolved,
    SolvedThreads

)
from .modules.aiModule import GenerateResponse
from .modules.helperClasses.report import ReportReciever
from .modules.helperClasses.shareQuestionHelper import ShareQuestionHelper
from .modules.helperClasses.textByPrefs import TextsByPrefs
from .modules.helperClasses.threadsHelper import ThreadHelper
from .modules.helperClasses.tokenVerificationHelper import TokenVerificationHelper
from .modules.helperClasses.userActivitys import (
    get_user_from_token,
    perform_search,
)
from .modules.helperClasses.userPrefsUpvotes import (
    handle_thread_vote,
    handle_comment_vote,
    handle_shared_vote,
    handle_thread_clicked
)
from .modules.helperClasses.userProfileLogin import (
    handle_existing_user,
    create_new_user,
)
from .schema import (
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
    BioAndJobSchema,
    JobListResponse
)

# Google Auth-Bibliotheken

# Initialisierung der API
api = NinjaAPI()

# Initialisierung logger
logger = logging.getLogger(__name__)


# texts based on prefs
@api.get("/Texts", response={200: List[ThreadResponseSchema], 401: dict, 404: NotFoundSchema, 500: dict})
def get_texts_for_user(request, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        user_pref_getter = TextsByPrefs(user)
        threads = user_pref_getter.get_weighted_threads(30)

        return 200, [
            ThreadHelper.format_thread_response(thread, request) for thread in threads
        ]

    except Http404:
        return 404, {"success": False, "message": "threadNotFound"}
    except Exception as e:
        logger.error(f"Error occurred while fetching threads for user {user.id}: {e}")
        return 500, {"success": False, "message": "exceptionFetchingThreadsForUser"}


# specific text by id
@api.get("/Texts/Id/{thread_id}", response={200: List[ThreadResponseSchema], 401: dict, 404: NotFoundSchema, 500: dict})
def get_texts_for_user(request, thread_id: int, authorization: str = Header(None)):
    # Check user authorization
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "userNotFound"}

    try:
        thread = get_object_or_404(Thread, id_thread=thread_id)
        formatted_response = ThreadHelper.format_thread_response(thread, request)

        return 200, [formatted_response]

    except Http404:
        return 404, {"success": False, "message": "threadNotFound"}
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching thread {thread_id} for user {user.id}: {e}")
        return 500, {"success": False, "message": "exceptionFetchingThreadForUser"}


# get all texts with a specific tag
@api.get("/Texts/Tag/{tag_name}", response={200: List[ThreadResponseSchema], 401: dict, 404: NotFoundSchema, 500: dict})
def get_texts_by_tag(request, tag_name: str, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        tag = get_object_or_404(Tag, name=tag_name)

        main_threads = Thread.objects.filter(main_tag=tag)
        subtag_threads = Thread.objects.filter(subtags=tag)

        threads = list(main_threads) + list(subtag_threads)
        formatted_response = [
            ThreadHelper.format_thread_response(thread, request) for thread in threads
        ]

        return 200, formatted_response

    except Http404:
        return 404, {"success": False, "message": f"tagNotFound"}
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching threads by tag '{tag_name}' for user {user.id}: {e}")
        return 500, {"success": False, "message": "exceptionFetchingThreadsByTagForUser"}


# new text add
@api.post("/AddNewText", response={201: ThreadResponseSchema, 401: dict, 400: dict, 500: dict})
def add_new_text(
        request,
        payload: Form[CreateThreadSchema],
        file: Optional[UploadedFile] = File(None),
        authorization: str = Header(None),
):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        main_tag = get_object_or_404(Tag, name=payload.main_tag)

        image_instance, image_url = ThreadHelper.handle_image_upload(file, user)

        with transaction.atomic():
            new_thread = ThreadHelper.create_thread(
                payload, user, main_tag, image_instance
            )

            response_data = {
                "success": True,
                "id_thread": new_thread.id_thread,
                "titel": new_thread.titel,
                "content": new_thread.content,
                "content_summary": new_thread.content_summary,
                "main_tag": str(new_thread.main_tag),
                "subtags": [str(tag) for tag in new_thread.subtags.all()],
                "image_url": image_url,
                "created_by": str(new_thread.created_by),
                "created_at": new_thread.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "upvotes": new_thread.upvotes,
            }

        return 201, response_data

    except ValueError as e:
        logger.warning(f"Validation error while adding new text for user {user.id}: {e}")
        return 400, {"success": False, "message": "exceptionValidateAddingNewTextForUser"}
    except Http404:
        return 404, {"success": False, "message": "tagNotFound"}
    except Exception as e:
        logger.error(f"Unexpected error occurred while adding new text for user {user.id}: {e}")
        return 500, {"success": False, "message": "exceptionAddingNewTextForUser"}


# Get Image for profile or thread
@api.post("/GetImages", response={201: ImageResponseSchema, 401: dict, 400: dict, 404: NotFoundSchema, 500: dict})
def get_image(request, payload: ImagePayload, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        if payload.content_type == "thread":
            object_from_id = get_object_or_404(Thread, id_thread=payload.object_id)
        elif payload.content_type == "userpicture":
            userProf = get_object_or_404(User, id=payload.object_id)
            object_from_id = get_object_or_404(UserProfile, user=userProf)
        else:
            return 400, {"success": False, "message": "invalidContentType"}

        image_instance = get_object_or_404(
            UploadedImage, image_id=object_from_id.image_url.image_id
        )

        if not image_instance.image:
            return 404, {"success": False, "message": "imageNotFound"}

        image_url = request.build_absolute_uri(image_instance.image.url)

        response_data = {
            "success": True,
            "image_url": image_url,
            "uploaded_by": str(image_instance.uploaded_by),
            "uploaded_at": image_instance.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

        return 201, response_data

    except Http404:
        return 404, {"success": False, "message": "requestedObjectOrImageNotFound"}
    except ValueError as e:
        logger.warning(f"invalidContentType")
        return 400, {"success": False, "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error fetching image for user {user.id}: {e}")
        return 500, {"success": False, "message": "exceptionFetchingIMageForUser"}


# Update a specific text
@api.post("/TextUpdate/{thread_id}",
          response={201: ThreadResponseSchema, 401: dict, 403: dict, 400: dict, 404: dict, 500: dict})
def update_text(
        request,
        thread_id: int,
        payload: Form[CreateThreadSchema],
        file: UploadedFile = File(None),
        authorization: str = Header(None),
):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        thread = get_object_or_404(Thread, id_thread=thread_id)

        if thread.created_by != user:
            return 403, {
                "success": False,
                "message": "userNotAuthorizedToUpdateThread",
            }

        with transaction.atomic():
            main_tag = (
                get_object_or_404(Tag, name=payload.main_tag)
                if payload.main_tag
                else None
            )

            ThreadHelper.update_thread_fields(thread, payload, main_tag)

            if file:
                try:
                    ThreadHelper.delete_existing_image(thread)
                    new_image_instance, _ = ThreadHelper.handle_image_upload(file, user)
                    thread.image_url = new_image_instance
                except Exception as e:
                    logger.error(f"File upload error for thread {thread_id}: {e}")
                    return 400, {"success": False, "message": f"fileUploadFailed"}

            thread.save()
            response_data = ThreadHelper.format_thread_response(thread, request)

        return 201, response_data

    except ValueError as e:
        logger.warning(f"Validation error for thread {thread_id}: {e}")
        return 400, {"success": False, "message": str(e)}
    except Http404 as e:
        logger.error(f"Resource not found: {e}")
        return 404, {"success": False, "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error occurred while updating thread {thread_id} for user {user.id}: {e}")
        return 500, {"success": False, "message": "exceptionUpdatingThreadForUser"}


# get important information for a job group
@api.get("/ImportantInformation/{job_group}",
         response={201: List[ImportandResponseSchema], 401: dict, 404: dict, 500: dict})
def get_important_by_job(request, job_group: str, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        job_group_obj = Job.objects.filter(name=job_group).first()
        if not job_group_obj:
            return 404, {"success": False, "message": "jobGroupNotFound"}

        important_infos = (
            ImportantInformation.objects.filter(
                id__in=job_group_obj.ImportantInformations.values_list("id", flat=True)
            )
            .order_by("-created_at")[:30]
            .prefetch_related("informationFrom")
        )

        response_data = [
            {
                "thread_id": info.informationFrom.id_thread,
                "title": info.informationFrom.titel,
                "summary": info.informationFrom.content_summary,
                "important_information": info.information,
            }
            for info in important_infos
        ]

        return 201, response_data

    except Http404 as e:
        logger.warning(f"Resource not found: {e}")
        return 404, {"success": False, "message": "resourcNotFound"}
    except Exception as e:
        logger.error(
            f"Unexpected error occurred while fetching important information for job group {job_group} by user {user.id}: {e}")
        return 500, {"success": False,
                     "message": "exceptuonFetchingImportantInformationForJobGroupByUser"}


# upvote everything
@api.post("/Upvote", response={200: dict, 201: dict, 401: dict, 404: dict, 500: dict})
def upvote_text(
        request, payload: UpvoteTypeResponse, authorization: str = Header(None)
):
    try:
        user = get_user_from_token(authorization)
        if user == None:
            return 404, {"success": False, "message": "userNotFound"}
        user_activity, created = UserActivity.objects.get_or_create(user=user)

        if payload.voteable == "thread":
            thread = get_object_or_404(Thread, id_thread=payload.voteable_id)
            handle_thread_vote(user_activity, thread, payload.upvoteType)

        elif payload.voteable == "comment":
            comment = get_object_or_404(Comment, comment_id=payload.voteable_id)
            handle_comment_vote(user_activity, comment, payload.upvoteType)

        elif payload.voteable == "shared":
            shared = get_object_or_404(SharedQuestion, shared_id=payload.voteable_id)
            handle_shared_vote(user_activity, shared, payload.upvoteType)

        try:
            user_activity.save()
        except Exception as e:
            logger.error(f"Error updating vote: {str(e)}")
            return 404, {"success": False, "message": "updatingVoteFailed"}

        return 201, {"success": True, "message": "upvoteTypeSuccessfull"}
    except Exception as e:
        logger.error(f"Error upvoting: {str(e)}")
        return 404, {"success": False, "message": "exceptionUpvoting"}


# delete text
@api.delete("/Text/{thread_id}", response={204: None, 401: dict, 403: dict, 404: dict, 500: dict})
def delete_text(request, thread_id: int, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        thread = ThreadHelper.get_thread_by_id(thread_id)
        if thread is None:
            return 404, {"success": False, "message": "threadNotFound"}

        if thread.created_by != user:
            return 403, {"success": False, "message": "forbiddenForThread"}

        thread.delete()
        return 204, None

    except Http404:
        logger.warning(f"Thread with ID '{thread_id}' not found for deletion")
        return 404, {"success": False, "message": "threadNotFound"}

    except Exception as e:
        logger.error(f"Unexpected error occurred while deleting thread {thread_id} by user {user.id}: {e}")
        return 500, {"success": False, "message": "exceptionDeletingThreadByUser"}


# Share, delet and get Questions
@api.post("/ShareQuestion", response={200: dict, 201: SharedQuestionResponseSchema, 401: dict, 404: dict, 500: dict})
def share_question(
        request, payload: CreateSharedQuestionSchema, authorization: str = Header(None)
):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        response_data = ShareQuestionHelper.create_shared_question(user, payload)
        return 201, response_data

    except Http404:
        logger.warning(f"Question not found or invalid data for user {user.id}")
        return 404, {"success": False, "message": "questionNotFound"}

    except HttpError as e:
        logger.error(f"HttpError occurred: {e.status_code}, {str(e)}")
        return e.status_code, {"success": False, "message": "httpError"}

    except Exception as e:
        logger.error(f"Unexpected error occurred while sharing question for user {user.id}: {e}")
        return 500, {"success": False, "message": "exceptionSharingQuestionForUser"}


# Get shared questions for the user
@api.get("/QuestionsShared", response={200: List[SharedQuestionResponseSchema], 401: dict, 404: dict, 500: dict})
def get_shared_questions_by_thread(request, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        response_data = ShareQuestionHelper.get_shared_questions_by_user(user)
        return 200, response_data

    except Http404:
        logger.warning(f"No shared questions found for user {user.id}")
        return 404, {"success": False, "message": "noSharedQuestionsFound"}

    except HttpError as e:
        logger.error(f"HttpError occurred while fetching shared questions for user {user.id}: {str(e)}")
        return e.status_code, {"success": False, "message": "httpErrrorFetchingSharedQuestionsForUser"}

    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching shared questions for user {user.id}: {e}")
        return 500, {"success": False,
                     "message": "exceptionFetchingSharedQuestionsForUser"}


# get all questions based on thread id
@api.get("/SharedQuestions/Thread/{id_thread}",
         response={200: List[SharedQuestionResponseSchema], 401: dict, 404: dict, 500: dict})
def get_shared_questions_by_thread(
        request, id_thread: int, authorization: str = Header(None)
):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        response_data = ShareQuestionHelper.get_shared_questions_by_thread(id_thread)
        if not response_data:
            return 404, {"success": False, "message": "noSharedQuestionsFoundForThread"}

        return 200, response_data

    except Http404:
        logger.warning(f"No shared questions found for thread ID {id_thread} for user {user.id}")
        return 404, {"success": False, "message": "noSharedQuestionsFound"}

    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching shared questions for thread ID {id_thread}: {e}")
        return 500, {"success": False, "message": "exceptionFetchingSharedQuestions"}


# delete shared question
@api.delete("/ManageSharedQuestion/{question_id}", response={204: dict, 401: dict, 404: dict, 500: dict})
def delete_shared_question(
        request, question_id: int, authorization: str = Header(None)
):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        deleted = ShareQuestionHelper.delete_shared_question(user, question_id)

        if not deleted:
            logger.warning(f"Shared question ID {question_id} not found for user {user.id}")
            return 404, {"success": False, "message": "sharedQuestionNotFound"}

        return 204, {"success": True, "message": "deleted"}

    except HttpError as e:
        logger.error(f"HttpError occurred while deleting shared question ID {question_id} for user {user.id}: {str(e)}")
        return e.status_code, {"success": False, "message": "exceptionDeletingSharedQuestion"}

    except Exception as e:
        logger.error(
            f"Unexpected error occurred while deleting shared question ID {question_id} for user {user.id}: {e}")
        return 500, {"success": False,
                     "message": "exceptionDeletingSharedQuestionIdForUser"}


# Token veryfizierung
@api.post(
    "/TokenVerifyLoginCreate", response={200: dict, 201: str, 404: NotFoundSchema}
)
def verify_token(request, payload: GoogleVerificationSchema):
    try:
        return TokenVerificationHelper.verify_and_create_user(payload)

    except Exception as e:
        logger.error(f"Error occurred while verifying token: {e}")
        return 404, {"success": False, "message": "exceptionVerifyingToken"}


@api.post("/CreateOrLoginUserWithMail", response={201: dict, 200: dict, 404: NotFoundSchema})
def create_user(
        request, payload: Form[CreateUserSchema], file: UploadedFile = File(None)
):
    try:
        user = User.objects.filter(
            Q(username=payload.username) | Q(email=payload.email)
        ).first()

        if user and check_password(payload.password, user.password):
            logger.warning("User logged in")
            return 200, handle_existing_user(user, file)
        elif payload.username and payload.email and payload.password:
            logger.warning("Creating new user")
            return 201, create_new_user(payload, file)
        else:
            return 404, {
                "success": False,
                "message": "invalidCredentials",
            }

    except Exception as e:
        return 404, {"success": False, "message": "exceptionCreatingLoginUser"}


### AI API Start###


# AI gens quiz
@api.get("/Ai/GenerateQuiz/{thread_id}/{language}", response={200: dict, 401: dict, 404: dict, 500: dict})
def generate_quiz(
        request, thread_id: int, language: str, authorization: str = Header(None)
):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    try:
        thread = get_object_or_404(Thread, id_thread=thread_id)

        generate_response = GenerateResponse()
        quiz_data = generate_response.create_quiz(thread.content, language)

        if "error" in quiz_data:
            logger.warning(
                f"Failed to generate quiz for thread {thread_id} in language {language}: {quiz_data['error']}")
            return 400, {"success": False, "message": quiz_data["error"]}

        logger.info(f"Generated quiz for thread {thread_id} in language {language} by user {user.id}")
        return 200, {"success": True, "data": quiz_data}

    except Http404:
        logger.warning(f"Thread ID {thread_id} not found for user {user.id}")
        return 404, {"success": False, "message": "threadNotFound"}

    except Exception as e:
        logger.error(f"Unexpected error occurred while generating quiz for thread ID {thread_id}: {e}")
        return 500, {"success": False, "message": "exceptionGeneratingQuizForThreadId"}


# AI correcting Questions and answers
@api.post("/Ai/CheckQuestions/{thread_id}/{language}", response={200: dict, 404: NotFoundSchema})
def check_answers(
        request,
        thread_id: int,
        language: str,
        payload: CheckQuestionSchema,
        authorization: str = Header(None),
):
    try:
        user = get_user_from_token(authorization)
        if user is None:
            return 404, {"success": False, "message": "userNotFound"}

        generate_response = GenerateResponse()
        thread = get_object_or_404(Thread, id_thread=thread_id)

        questions = payload.questions
        answers = payload.answers

        if not questions or not answers:
            logger.warning(f"Questions or answers not provided for thread {thread.id}")
            return 404, {
                "success": False,
                "message": "questionsOrAnswersNotProvided",
            }

        # AI response with score and answers
        answer_data = generate_response.check_answers(
            thread.content, questions, answers, language
        )

        if "error" in answer_data:
            return {"success": False, "message": answer_data["error"]}

        # Save to QuizAbsolved model
        quiz_entries = []
        for i, question in enumerate(questions):
            quiz_entry = QuizAbsolved(
                Question=question,
                AnswerFromUser=answers[i],
                AiAnswer=answer_data["questions"][i],
                score=answer_data["score"]
            )
            quiz_entry.save()
            quiz_entries.append(quiz_entry)

        # Save to SolvedThreads model
        solved_thread = SolvedThreads.objects.create(Created_At=timezone.now())
        solved_thread.Threads.add(thread)
        solved_thread.QuizAbsolved.set(quiz_entries)
        solved_thread.save()

        logger.info(f"Checked and saved answers for thread {thread.id_thread}")
        return {"success": True, "data": answer_data}

    except Exception as e:
        logger.error(f"Error occurred while fetching threads: {e}")
        return 404, {"success": False, "message": "exceptionFetchingThreads"}


# choosing 30 usinque questions from shared
@api.get("/Ai/Gentop/{thread_id}/{language}", response={200: dict, 404: NotFoundSchema})
def gen_random_top(request, thread_id, language, authorization: str = Header(None)):
    try:
        user = get_user_from_token(authorization)
        if user is None:
            return 404, {"success": False, "message": "userNotFound"}

        generate_response = GenerateResponse()
        thread = get_object_or_404(Thread, id_thread=thread_id)
        logger.info(f"Edit action for thread {thread.id_thread}")

        questions_queryset = SharedQuestion.objects.filter(thread=thread).order_by(
            "-created_at"
        )
        question_count = questions_queryset.count()

        if question_count == 0:
            logger.error(f"No questions found for thread {thread_id}.")
            return 404, {"success": False, "message": "noQuestionsFoundForThread"}

        max_questions_to_use = min(question_count, 30)
        questions = [
            question.content for question in questions_queryset[:max_questions_to_use]
        ]

        top_quiz_response = generate_response.generate_random_top(
            thread.content, questions, language
        )
        if "error" in top_quiz_response:
            return {"success": False, "message": top_quiz_response["error"]}

        logger.info(f"Generated random top quiz for thread {thread.id_thread}")
        return {"success": True, "data": top_quiz_response}
    except Exception as e:
        logger.error(f"Error occurred while fetching threads: {e}")
        return 404, {"success": False, "message": "exceptionFetchingThreads"}


# AI chosing prefs for you
@api.post("/Ai/WeightPrefs", response={200: dict, 201: dict, 400: dict, 401: dict, 500: dict})
def weight_user_prefs(
        request, payload: UserPrefsResponse, authorization: str = Header(None)
):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    logger.info(f"User {user.id} is weighting preferences")

    chosen_prefs = payload.prefs
    UserPreferences.objects.filter(user=user).delete()

    try:
        generate_response = GenerateResponse()
        user_pref_response = generate_response.weight_userPrefs(chosen_prefs)

        if isinstance(user_pref_response, str):
            try:
                user_pref_response = json.loads(user_pref_response)
            except json.JSONDecodeError:
                logger.error("Invalid JSON response from weight_userPrefs")
                return 400, {"success": False, "message": "invalidJsonResponseFromWeigthUserPrefs"}

        saved_prefs = []
        for pref in user_pref_response.get("preferences", []):
            preference = pref.get("preference")
            weight = pref.get("weight")

            user_pref = UserPreferences.objects.create(
                user=user, preference=preference, weight=weight
            )

            saved_prefs.append(
                {"preference": user_pref.preference, "weight": user_pref.weight}
            )

        return 201, {"success": True, "preferences": saved_prefs}

    except Exception as e:
        logger.error(f"Error occurred while weighting user preferences for user {user.id}: {e}")
        return 500, {"success": False,
                     "message": "exceptionWeightingUserPreferencesForUser"}


# Ai gens tags for text
@api.post("/Ai/GenerateTags", response={200: dict, 201: dict, 400: dict, 401: dict, 500: dict})
def generate_tags(request, payload: TagGivingSchema, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    logger.info(f"User {user.id} is generating tags for provided content")

    try:
        generate_response = GenerateResponse()

        tags_list = list(Tag.objects.values_list("name", flat=True))
        logger.debug(f"Existing tags retrieved: {tags_list}")

        tags_response = generate_response.evaluate_text(tags_list, payload.content)
        logger.info("Tags generated successfully")

        return 201, {"success": True, "tags": tags_response}

    except Exception as e:
        logger.error(f"Error occurred while generating tags for user {user.id}: {e}")
        return 500, {"success": False, "message": "exceptionGeneratingTagsForUser"}


@api.post("/Ai/Summarize/{language}", response={200: dict, 400: dict, 401: dict, 500: dict})
def summarize_ai(
        request, language: str, payload: TagGivingSchema, authorization: str = Header(None)
):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    logger.info(f"User {user.id} is summarizing text in {language}")

    try:
        generate_response = GenerateResponse()
        result = generate_response.summarize_text(
            payload.content, payload.titel, language
        )

        logger.info("Text summarized successfully")
        return 200, {"success": True, "summary": result}

    except ValueError as ve:
        logger.error(f"Value error while summarizing: {ve}")
        return 400, {"success": False, "message": "invalidInputData"}
    except Exception as e:
        logger.error(f"Error occurred while summarizing text for user {user.id}: {e}")
        return 500, {"success": False, "message": "couldNotSummarizeTextForUser"}


# Funktion for data creation
@api.post("/Ai/SummarizeAndTag/{language}", response={200: dict, 400: dict, 401: dict, 500: dict})
def summariezeandtag(
        request, language: str, payload: TagGivingSchema, authorization: str = Header(None)
):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    logger.info(f"User {user.id} is summarizing and tagging text in {language}")

    try:
        tags_list = list(Tag.objects.values_list("name", flat=True))

        logger.info("Generating summary and tags for the provided content")
        generate_response = GenerateResponse()

        result = generate_response.summarieze_tags(
            payload.content, payload.titel, language, tags_list
        )

        logger.info("Successfully summarized and tagged the text")
        return 200, {"success": True, "data": result}

    except ValueError as ve:
        logger.error(f"Value error occurred: {ve}")
        return 400, {"success": False, "message": "invalidInputData"}
    except Exception as e:
        logger.error(f"Unexpected error while summarizing and tagging for user {user.id}: {e}")
        return 500, {"success": False, "message": "couldNotSummarizeAndTagUser"}


# Preference management
@api.delete("/MangePrefs", response={200: dict, 201: str, 404: NotFoundSchema})
def delete_user_prefs(request, authorization: str = Header(None)):
    try:
        user = get_user_from_token(authorization)
        if user == None:
            return 404, {"success": False, "message": "userNotFound"}

        deleted, _ = UserPreferences.objects.filter(user=user).delete()

        return {
            "success": True,
            "message": f"{deleted} preferences deleted for {user.username}",
        }
    except Exception as e:
        logger.error(f"Error occurred while fetching threads: {e}")
        return 404, {"success": False, "message": "couldNotFetchThreads"}


# get or show preferences
@api.get("/Prefs", response={200: dict, 201: str, 404: NotFoundSchema})
def get_user_prefs(request, authorization: str = Header(None)):
    try:
        user = get_user_from_token(authorization)
        if user == None:
            return 404, {"success": False, "message": "userNotFound"}

        user_prefs = UserPreferences.objects.filter(user=user)

        prefs_list = [
            {"preference": pref.preference, "weight": pref.weight}
            for pref in user_prefs
        ]

        return 201, {"success": True, "preferences": prefs_list}
    except Exception as e:
        return 404, {"success": False, "message": "couldNotGetPreferences"}


# get or fill tags
@api.get("/Tags", response={200: dict, 401: dict, 500: dict})
def filldatawithtags(request, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    logger.info(f"User {user.username} requested to fetch tags.")

    try:
        tags_data = {
            "Tags": [
                "Technology", "Science", "Music", "Culture", "Sports",
                "Movies and Series", "Education", "Literature", "History",
                "Travel", "Nature and Environment", "Fashion", "Culinary",
                "Psychology", "Finance", "Space Exploration", "Gaming",
                "Creativity and Design", "Art",
            ]
        }

        for tag_name in tags_data["Tags"]:
            Tag.objects.get_or_create(name=tag_name)

        all_tags = Tag.objects.all()

        return {
            "success": True,
            "tags": [tag.name for tag in all_tags],
        }

    except Exception as e:
        logger.error(f"Error occurred while fetching tags for user {user.username}: {e}")
        return 500, {"success": False, "message": "couldNotFetchTagsForUser"}


# delete one specific user
@api.delete("/ManageUser", response={200: dict, 201: dict, 404: NotFoundSchema})
def delete_user(
        request, payload: PasswordConfirmationSchema, authorization: str = Header(None)
):
    try:
        user = get_user_from_token(authorization)
        if user == None:
            return 404, {"success": False, "message": "userNotFound"}

        if not check_password(payload.password, user.password):
            return 404, {"error": "Incorrect password."}

        with transaction.atomic():

            threads = Thread.objects.filter(created_by=user)
            for thread in threads:
                thread.comments.all().delete()
                thread.shared_questions.all().delete()
            threads.delete()

            UserActivity.objects.filter(user=user).delete()
            ReportModel.objects.filter(reported_by=user).delete()
            SearchRequests.objects.filter(user=user).delete()
            UserPreferences.objects.filter(user=user).delete()
            UserProfile.objects.filter(user=user).delete()
            UploadedImage.objects.filter(uploaded_by=user).delete()

            user.delete()

        return 201, {
            "success": True,
            "message": f"Successfully deleted user {user.username} and their related data.",
        }

    except Exception as e:
        logger.error(f"Error occurred while fetching threads: {e}")
        return 404, {"success": False, "message": "couldNotFetchThreadsFromUser"}


@api.post("/Report", response={200: dict, 201: str, 404: NotFoundSchema})
def report_content(request, payload: ReportPayload, authorization: str = Header(None)):
    try:
        user = get_user_from_token(authorization)
        if user == None:
            return 404, {"success": False, "message": "userNotFound"}
        report_create = ReportReciever()
        return report_create.create_report(user, payload)
    except Exception as e:
        logger.error(f"Error occurred while fetching threads: {e}")
        return 404, {"success": False, "message": "couldNotFetchThreadsFromReport"}


# TODO: COMMENTSECTION


# search working here is the payload example:
# {
#     "search_term": "Tech",
#     "filters": {
#         "user": true,
#         "tags": true,
#         "threads": true,
#         "comments": false
#     }
# }
# search working here is the payload example:
# {
#     "search_term": "Tech",
#     "filters": {
#         "user": true,
#         "tags": true,
#         "threads": true,
#         "comments": false
#     }
# }
@api.post("/Search", response={200: dict, 201: SearchResponseSchema, 404: NotFoundSchema})
def search_endpoint(
        request: str, payload: SearchRequest, authorization: str = Header(None)
):
    try:
        user = get_user_from_token(authorization)
        if user == None:
            return 404, {"success": False, "message": "userNotFound"}

        if not user:
            raise HttpError(404, "userNotFound")

        search_results = perform_search(payload.search_term, payload.filters.dict(), request)

        search_request = SearchRequests.objects.create(
            user=user,
            search_term=payload.search_term,
            search_result=search_results,
            timestamp=timezone.now(),
        )

        return 200, {
            "success": True,
            "searchresult": search_results,
            "search_id": search_request.search_id,
        }
    except Exception as e:
        return 404, {"success": False, "message": "couldNotSearchUser"}


@api.post(
    "/Users/Find", response={200: dict, 201: PublicUserResponse, 404: NotFoundSchema}
)
def get_user_from_username(
        request: str, payload: UserRequest, authorization: str = Header(None)
):
    try:
        user = get_user_from_token(authorization)
        if user == None:
            return 404, {"success": False, "message": "userNotFound"}

        if not user:
            raise HttpError(404, "userNotFound")

        try:
            user_activity = UserActivity.objects.get(user=user)
        except UserActivity.DoesNotExist:
            user_activity = None

        written_threads = Thread.objects.filter(created_by=user)
        shared_questions = SharedQuestion.objects.filter(created_by=user)
        user_reports = ReportModel.objects.filter(reported_by=user)
        userprofile = UserProfile.objects.get(user=user)
        job = userprofile.job
        important_infos = []
        if job != None:
            important_infos = job.ImportantInformations.all().order_by("-created_at")[
                              :30
                              ]
        if payload.username == user.username:
            response_data = {
                "username": user.username,
                "user_id": user.id,
                "bio": userprofile.bio,
                "job": job.name if job else None,
                "importantInfo": [info.information for info in important_infos],
                "upvoted_threads": (
                    [thread.id_thread for thread in user_activity.upvotedThreads.all()]
                    if user_activity
                    else []
                ),
                "downvoted_threads": (
                    [
                        thread.id_thread
                        for thread in user_activity.downvotedThreads.all()
                    ]
                    if user_activity
                    else []
                ),
                "upvoted_comments": (
                    [
                        comment.comment_id
                        for comment in user_activity.upvotedComments.all()
                    ]
                    if user_activity
                    else []
                ),
                "downvoted_comments": (
                    [
                        comment.comment_id
                        for comment in user_activity.downvotedComments.all()
                    ]
                    if user_activity
                    else []
                ),
                "upvoted_shared_questions": (
                    [
                        question.shared_id
                        for question in user_activity.upvotedSharedQuestions.all()
                    ]
                    if user_activity
                    else []
                ),
                "downvoted_shared_questions": (
                    [
                        question.shared_id
                        for question in user_activity.downvotedSharedQuestions.all()
                    ]
                    if user_activity
                    else []
                ),
                "written_threads": [
                    {
                        "id": thread.id_thread,
                        "title": thread.titel,
                        "content": thread.content,
                    }
                    for thread in written_threads
                ],
                "shared_questions": [
                    {"id": question.shared_id, "content": question.content}
                    for question in shared_questions
                ],
                "reports": [
                    {
                        "report_id": report.report_id,
                        "type": report.reported_type,
                        "reason": report.reported_why,
                    }
                    for report in user_reports
                ],
            }
        else:
            user = User.objects.get(username=payload.username)
            userprofile = UserProfile.objects.get(user=user)
            try:
                user_activity = UserActivity.objects.get(user=user)
            except UserActivity.DoesNotExist:
                user_activity = None

            response_data = {
                "username": user.username,
                "user_id": user.id,
                "bio": userprofile.bio,
                "job": userprofile.job.name if userprofile.job else None,
                "upvoted_threads": (
                    [thread.id_thread for thread in user_activity.upvotedThreads.all()]
                    if user_activity
                    else []
                ),
                "written_threads": [
                    {
                        "id": thread.id_thread,
                        "title": thread.titel,
                        "content": thread.content,
                    }
                    for thread in written_threads
                ],
                "shared_questions": [
                    {"id": question.shared_id, "content": question.content}
                    for question in shared_questions
                ],
            }

        return response_data

    except Exception as e:
        return 404, {"success": False, "message": "couldNotFoundUser"}


class UserDetails(Schema):
    first_name: str
    last_name: str
    birthdate: date


@api.post("/Users/Image")
def create_user(request, details: Form[UserDetails], file: UploadedFile = File(...)):
    image_data = file.read()

    return {
        "details": details.dict(),
        "file": "Image received successfully",
        "file_size": len(image_data),
    }


# comments
@api.post(
    "/Threads/{thread_id}/Comment",
    response={201: CommentResponseSchema, 404: NotFoundSchema},
)
def add_comment(
        request,
        thread_id: int,
        payload: CommentCreateSchema,
        authorization: str = Header(None),
):
    try:
        user = get_user_from_token(authorization)
        if user == None:
            return 404, {"success": False, "message": "userNotFound"}
        thread = get_object_or_404(Thread, id_thread=thread_id)

        comment = Comment.objects.create(
            content=payload.content,
            thread=thread,
            created_by=user,
        )

        return 201, {
            "success": True,
            "comment_id": comment.comment_id,
            "content": comment.content,
            "created_at": comment.created_at,
            "created_by": user.username,
            "upvotes": comment.upvotes,
        }
    except Exception as e:
        return 404, {"success": False, "message": "couldNotAddComments"}


@api.get(
    "/Threads/{thread_id}/ShowComments",
    response={201: List[CommentResponseSchema], 404: NotFoundSchema},
)
def get_comments(request, thread_id: int, authorization: str = Header(None)):
    try:
        user = get_user_from_token(authorization)
        if user == None:
            return 404, {"success": False, "message": "userNotFound"}
        thread = get_object_or_404(Thread, id_thread=thread_id)

        comments = Comment.objects.filter(thread=thread).order_by("-created_at")

        return 201, [
            {
                "success": True,
                "comment_id": comment.comment_id,
                "content": comment.content,
                "created_at": comment.created_at,
                "created_by": comment.created_by.username,
                "upvotes": comment.upvotes,
            }
            for comment in comments
        ]
    except Exception as e:
        return 404, {"success": False, "message": "couldNotGetComments"}


@api.put(
    "/EditComments/{comment_id}",
    response={201: CommentResponseSchema, 404: NotFoundSchema},
)
def edit_comment(
        request,
        comment_id: int,
        payload: CommentCreateSchema,
        authorization: str = Header(None),
):
    try:
        user = get_user_from_token(authorization)
        if user == None:
            return 404, {"success": False, "message": "userNotFound"}
        comment = get_object_or_404(Comment, comment_id=comment_id, created_by=user)

        comment.content = payload.content
        comment.save()

        return 201, {
            "success": True,
            "comment_id": comment.comment_id,
            "content": comment.content,
            "created_at": comment.created_at,
            "created_by": comment.created_by.username,
            "upvotes": comment.upvotes,
        }
    except Exception as e:
        return 404, {"success": False, "message": "exceptionTryingToEditComment"}


@api.delete("/ManageComments/{comment_id}", response={201: dict, 404: NotFoundSchema})
def delete_comment(request, comment_id: int, authorization: str = Header(None)):
    try:
        user = get_user_from_token(authorization)
        if user is None:
            return 404, {"success": False, "message": "userNotFound"}

        comment = get_object_or_404(Comment, comment_id=comment_id, created_by=user)

        comment.delete()
        return 201, {"success": True, "message": "commentDeletedSucessfull"}
    except Exception as e:
        return 404, {"success": False, "message": "exceptionTryingToDeleteComment"}


@api.get("/Clicked/{thread_id}", response={201: dict, 404: NotFoundSchema})
def click_thread(request, thread_id: int, authorization: str = Header(None)):
    try:
        user = get_user_from_token(authorization)
        if user is None:
            return 404, {"success": False, "message": "userNotFound"}

        return handle_thread_clicked(thread_id, user, 1.3)

    except Exception as e:
        return 404, {"success": False, "message": "exceptionTryingToClickThread"}


@api.get("/Job/List", response={200: JobListResponse, 401: dict, 404: NotFoundSchema})
def job_list(request, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    jobs = Job.objects.values_list('name', flat=True)
    return 200, {"jobs": list(jobs)}


@api.post("/Job", response={201: dict, 401: dict, 404: NotFoundSchema})
def add_job_bio(request, payload: BioAndJobSchema, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    if user is None:
        return 401, {"success": False, "message": "unauthorizedUserNotFound"}

    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if payload.jobname:
        job = Job.objects.filter(name=payload.jobname).first()
        if not job:
            return 404, {"success": False, "message": "jobNotFound"}
        user_profile.job = job

    if payload.bio is not None:
        user_profile.bio = payload.bio

    user_profile.save()

    return 201, {"success": True, "message": "jobOrBioUpdated"}
