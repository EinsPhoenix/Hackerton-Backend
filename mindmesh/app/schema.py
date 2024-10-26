from datetime import datetime
from ninja import Schema
from typing import List, Optional,Literal
from pydantic import BaseModel, EmailStr, Field

class GetTextsSchema(Schema):
    titel: str
    content: str
    content_summary: str
    main_tag: str
    subtags: Optional[List[str]]
    image_url: Optional[str]
    created_at: datetime
    created_by: str
    upvotes: int

class CreateThreadSchema(Schema):
    titel: str
    content: str
    content_summary: Optional[str]
    main_tag: str
    subtags: Optional[List[str]] = None


class UpdateThreadSchema(Schema):
    titel: Optional[str]
    content: Optional[str]
    content_summary: Optional[str]
    main_tag: Optional[str]
    subtags: Optional[List[str]] = None



class CreateUserSchema(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str


class ThreadResponseSchema(Schema):
    success: Optional[bool] = True
    id_thread: int
    titel: str
    content: str
    content_summary: str
    main_tag: str
    subtags: list[str]
    created_by: str
    created_at: datetime
    upvotes: int
    image_url: Optional[str]

class ImportandResponseSchema(BaseModel):
    thread_id: int
    titel: str
    summary: str
    important_information: list[str]= None


class CheckQuestionSchema(Schema):
    questions: List[str]
    answers: List[str]

class TagGivingSchema(Schema):
    titel:str
    content:str


class Preference(BaseModel):
    preference: str
    chosen: bool

class UserPrefsResponse(BaseModel):
    prefs: List[Preference]

class UpvoteTypeResponse(Schema):
    voteable: str
    voteable_id: int
    upvoteType: str

class CreateSharedQuestionSchema(BaseModel):
    thread_id: int
    content: str

class SharedQuestionResponseSchema(BaseModel):
    success: bool
    shared_id: int
    thread_id: int
    content: str
    created_at: str
    created_by: str
    upvotes: int


class PasswordConfirmationSchema(Schema):
    password: str

class UserRequest(Schema):
    username: str


class ThreadSchema(Schema):
    id: int
    title: str
    content: str

class SharedQuestionSchema(Schema):
    id: int
    content: str

class ReportSchema(Schema):
    report_id: int
    type: str
    reason: str


class PublicUserResponse(Schema):
    username: str
    user_id: int
    bio: str
    job: str
    importantInfo: List[str]
    upvoted_threads: List[int]
    written_threads: List[ThreadSchema]
    shared_questions: List[SharedQuestionSchema]
    downvoted_threads: Optional[List[int]] = None
    upvoted_comments: Optional[List[int]] = None
    downvoted_comments: Optional[List[int]] = None
    upvoted_shared_questions: Optional[List[int]] = None
    downvoted_shared_questions: Optional[List[int]] = None
    reports: Optional[List[ReportSchema]] = None


class UserSchema(BaseModel):
    success: bool
    id: int
    username: str
    email: str
    token: Optional[str]

class MessageResponseSchema(Schema):
    success: bool
    message: str
    token: Optional[str]

class CommentSchema(BaseModel):
    comment_id: str
    content: str
    created_at: str
    created_by: str
    thread_id: int
    upvotes: int



class ImportantInformationSchema(BaseModel):
    information: str
    created_at: str  # Use string to represent the date

class JobSchema(BaseModel):
    name: str
    important_information: List[ImportantInformationSchema]

class SearchFilters(BaseModel):
    user: bool = False
    tags: bool = False
    threads: bool = False
    comments: bool = False
    jobs: bool = False  # Add jobs filter

class SearchRequest(BaseModel):
    search_term: str
    filters: SearchFilters

class SearchResultsSchema(BaseModel):
    threadsmatching: List[GetTextsSchema]
    commentsmatching: List[CommentSchema]
    sharedQuestions: List[SharedQuestionSchema]
    users: List[UserSchema]
    jobs: List[JobSchema]

class SearchResponseSchema(BaseModel):
    success: bool
    searchresult: SearchResultsSchema
    search_id: int



class ReportPayload(BaseModel):
    reported_why: str = Field(..., min_length=1, description="Begründung für das Report")
    content_type: Literal["thread", "comment", "shared"]
    reported_object_id: int

class ImagePayload(BaseModel):
    content_type: Literal["thread", "userpicture"]
    object_id: int


class ImageResponseSchema(BaseModel):
    success: bool
    image_url: str
    uploaded_by: str
    uploaded_at: str



class NotFoundSchema(Schema):
    success: bool = False
    message: str

class CommentResponseSchema(Schema):
    success: bool
    comment_id: int
    content: str
    created_at: datetime
    created_by: str
    upvotes: int

class GoogleVerificationSchema(Schema):
    token: str
    devicetype: Literal["android", "web", "ios"]

class CommentCreateSchema(Schema):
    content: str

