from django.contrib import admin
from django.contrib.auth.models import User
from django.db import transaction
from .models import QuizAbsolved, SolvedThreads, UserPreferences, UserProfile, Tag, Thread, Comment, SharedQuestion, UserActivity, ReportModel, SearchRequests, UploadedImage, CompanyProfile, Job, ImportantInformation
from django.db.models import Q


'''Section for Custom Filters inside the Admin Panel'''

#Extra Input Filter
class InputFilter(admin.SimpleListFilter):
    template = 'input_filter.html'

    def lookups(self, request, model_admin):
        # Dummy-Lookup, um den Filter anzuzeigen
        return ((),)

    def choices(self, changelist):
        # Nur die "Alle"-Option anzeigen, um den Filter zurückzusetzen
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice

class CreatedAtFilter(InputFilter):
    title = 'Created At'
    parameter_name = 'created_at'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(created_at__icontains=self.value())

class CreatedByFilter(InputFilter):
    title = 'Created By'
    parameter_name = 'created_by'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(created_by__username__icontains=self.value())
        
class NameFilter(InputFilter):
    title = 'Name'
    parameter_name = 'name'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(name__icontains=self.value())
        
class InterestsFilter(InputFilter):
    title = 'Interests'
    parameter_name = 'interests'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(interests__icontains=self.value())
        
class BrancheFilter(InputFilter):
    title = 'Branche'
    parameter_name = 'branche'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(branche__icontains=self.value())
        
class UserFilter(InputFilter):
    title = 'User'
    parameter_name = 'user'

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__username__icontains=self.value())
        return queryset
        
class PreferenceFilter(InputFilter):
    title = 'Preference'
    parameter_name = 'preference'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(preference__icontains=self.value())
        
class WeightFilter(InputFilter):
    title = 'Weight'
    parameter_name = 'weight'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(weight__icontains=self.value())
        
class ImageFilter(InputFilter):
    title = 'Image'
    parameter_name = 'image'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(image__icontains=self.value())
        
class UploadedAtFilter(InputFilter):
    title = 'Uploaded At'
    parameter_name = 'uploaded_at'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(uploaded_at__icontains=self.value())
        
class UploadedByFilter(InputFilter):
    title = 'Uploaded By'
    parameter_name = 'uploaded_by'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(uploaded_by__username__icontains=self.value())
        
class TitelFilter(InputFilter):
    title = 'Titel'
    parameter_name = 'titel'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(titel__icontains=self.value())
        
class ContentFilter(InputFilter):
    title = 'Content'
    parameter_name = 'content'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(content__icontains=self.value())
        
class ContentSummaryFilter(InputFilter):
    title = 'Content Summary'
    parameter_name = 'content_summary'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(content_summary__icontains=self.value())
        
class MainTagFilter(InputFilter):
    title = 'Main Tag'
    parameter_name = 'main_tag'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(main_tag__name__icontains=self.value())
        
class SubtagsFilter(InputFilter):
    title = 'Subtags'
    parameter_name = 'subtags'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(subtags__name__icontains=self.value())

class ImageUrlFilter(InputFilter):
    title = 'Image Url'
    parameter_name = 'image_url'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(image_url__image__icontains=self.value())
        
class UpvotesFilter(InputFilter):
    title = 'Upvotes'
    parameter_name = 'upvotes'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(upvotes__icontains=self.value())
        
class InformationFilter(InputFilter):
    title = 'Information'
    parameter_name = 'information'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(information__icontains=self.value())
        
class InformationFromFilter(InputFilter):
    title = 'Information From'
    parameter_name = 'informationFrom'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(informationFrom__titel__icontains=self.value())
        
class ImportantInformationsFilter(InputFilter):
    title = 'Important Informations'
    parameter_name = 'ImportantInformations'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(Q(ImportantInformations__information__icontains=self.value()) |
                                   Q(ImportantInformations__informationFrom__titel__icontains=self.value())
                                   )
class QuestionFilter(InputFilter):
    title = 'Question'
    parameter_name = 'Question'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(Question__icontains=self.value())
        
class AnswerFromUser(InputFilter):
    title = 'Answer From User'
    parameter_name = 'AnswerFromUser'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(AnswerFromUser__icontains=self.value())
        
class AiAnswerFilter(InputFilter):
    title = 'Ai Answer'
    parameter_name = 'AiAnswer'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(AiAnswer__icontains=self.value())
        
class ScoreFilter(InputFilter):
    title = 'Score'
    parameter_name = 'score'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(score__icontains=self.value())
        
class ThreadsFilter(InputFilter):
    title = 'Thread'
    parameter_name = 'thread'

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(Threads__titel__icontains=self.value())
        return queryset
        
class QuizAbsolvedFilter(InputFilter):
    title = 'Quiz Absolved'
    parameter_name = 'quiz_absolved'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter( Q(QuizAbsolved__Question__icontains=self.value())|
                                    Q(QuizAbsolved__AnswerFromUser__icontains=self.value())|
                                    Q(QuizAbsolved__AiAnswer__icontains=self.value())
                                   )
        
class BioFilter(InputFilter):
    title = 'Bio'
    parameter_name = 'bio'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(bio__icontains=self.value())
        
class TokenFilter(InputFilter):
    title = 'Token'
    parameter_name = 'token'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(token__icontains=self.value())
        
class JobFilter(InputFilter):
    title = 'Job'
    parameter_name = 'job'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(job__name__icontains=self.value())
        
class SolvedThreadsFilter(InputFilter):
    #TODO Hier nochmal schauen ob das so passt
    #TODO IST NAHEZU UNMÖGLICH wird gemacht wenn am Ende des Projekts noch Zeit ist
    title = 'Solved Threads'
    parameter_name = 'solvedThreads'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(solvedThreads__icontains=self.value())
        
class ThreadFilter(InputFilter):
    title = 'Thread'
    parameter_name = 'thread'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(thread__titel__icontains=self.value())
        
class ReportedWhyFilter(InputFilter):
    title = 'Reported Why'
    parameter_name = 'reported_why'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(reported_why__icontains=self.value())
        
        
class UpvoatedThreadsFilter(InputFilter):
    title = 'Upvoted Threads'
    parameter_name = 'upvotedThreads'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(upvotedThreads__icontains=self.value())
        
class DownvotedThreadsFilter(InputFilter):
    title = 'Downvoted Threads'
    parameter_name = 'downvotedThreads'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(downvotedThreads__icontains=self.value())
        
class UpvotedCommentsFilter(InputFilter):
    title = 'Upvoted Comments'
    parameter_name = 'upvotedComments'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(upvotedComments__icontains=self.value())
        
class DownvotedCommentsFilter(InputFilter):
    title = 'Downvoted Comments'
    parameter_name = 'downvotedComments'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(downvotedComments__icontains=self.value())
        
class UpvotedSharedQuestionsFilter(InputFilter):
    title = 'Upvoted Shared Questions'
    parameter_name = 'upvotedSharedQuestions'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(upvotedSharedQuestions__icontains=self.value())
        
class DownvotedSharedQuestionsFilter(InputFilter):
    title = 'Downvoted Shared Questions'
    parameter_name = 'downvotedSharedQuestions'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(downvotedSharedQuestions__icontains=self.value())
        
class ReportedByFilter(InputFilter):
    title = 'Reported By'
    parameter_name = 'reported_by'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(reported_by__username__icontains=self.value())
        
class ReportedAtFilter(InputFilter):
    title = 'Reported At'
    parameter_name = 'reported_at'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(reported_at__icontains=self.value())
        
class ContentTypeFilter(InputFilter):
    title = 'Content Type'
    parameter_name = 'content_type'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(   
                                    Q(content_type__model__icontains=self.value()) |
                                    Q(content_type__app_label__icontains=self.value())
                                   )
        
class ObjectIDFilter(InputFilter):
    title = 'Object ID'
    parameter_name = 'object_id'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(object_id__icontains=self.value())
        
class ReportedTypeFilter(InputFilter):
    title = 'Reported Type'
    parameter_name = 'reported_type'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(reported_type__icontains=self.value())
        
class SearchTermFilter(InputFilter):
    title = 'Search Term'
    parameter_name = 'search_term'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(search_term__icontains=self.value())
        
class TimestampFilter(InputFilter):
    title = 'Timestamp'
    parameter_name = 'timestamp'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(timestamp__icontains=self.value())
        
class searchResultFilter(InputFilter):
    title = 'searchResult'
    parameter_name = 'searchResult'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(search_result__icontains=self.value())
        
class UpvotedThreadsFilter(InputFilter):
    title = 'Upvoted Threads'
    parameter_name = 'upvotedThreads'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(upvotedThreads__titel__icontains=self.value())
        
class DownvotedThreadsFilter(InputFilter):
    title = 'Downvoted Threads'
    parameter_name = 'downvotedThreads'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(downvotedThreads__titel__icontains=self.value())
        
class UpvotedCommentsFilter(InputFilter):
    title = 'Upvoted Comments'
    parameter_name = 'upvotedComments'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(upvotedComments__content__icontains=self.value())
        
class DownvotedCommentsFilter(InputFilter):
    title = 'Downvoted Comments'
    parameter_name = 'downvotedComments'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(downvotedComments__content__icontains=self.value())
        
class UpvotedSharedQuestionsFilter(InputFilter):
    title = 'Upvoted Shared Questions'
    parameter_name = 'upvotedSharedQuestions'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(upvotedSharedQuestions__content__icontains=self.value()) 

class DownvotedSharedQuestionsFilter(InputFilter):
    title = 'Downvoted Shared Questions'
    parameter_name = 'downvotedSharedQuestions'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(downvotedSharedQuestions__content__icontains=self.value())
  



'''Custom Filter Section Ends Here'''

# Register your models here.

@admin.action(description='Tags für alle Benutzer hinzufügen')
def fill_data_with_tags(modeladmin, request, queryset):
    tags_data = [
        "Technology", "Science", "Music", "Culture", "Sports",
        "Movies and Series", "Education", "Literature", "History",
        "Travel", "Nature and Environment", "Fashion", "Culinary",
        "Psychology", "Finance", "Space Exploration", "Gaming",
        "Creativity and Design", "Art"
    ]

    for tag_name in tags_data:
        Tag.objects.get_or_create(name=tag_name)

    modeladmin.message_user(request, "Tags wurden erfolgreich hinzugefügt.")

@admin.action(description='Alle Benutzer und deren Daten löschen (außer Superuser)')
def delete_all_users(modeladmin, request, queryset):
    with transaction.atomic():
        normal_users = queryset.exclude(is_superuser=True)
        user_count = normal_users.count()

        Thread.objects.filter(created_by__in=normal_users).delete()
        UserActivity.objects.filter(user__in=normal_users).delete()
        UserPreferences.objects.filter(user__in=normal_users).delete()
        UserProfile.objects.filter(user__in=normal_users).delete()
        SearchRequests.objects.filter(user__in=normal_users).delete()
        ReportModel.objects.filter(reported_by__in=normal_users).delete()
        normal_users.delete()

    modeladmin.message_user(request, f"Erfolgreich {user_count} normale Benutzer und deren zugehörige Daten gelöscht.")


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserPreferences._meta.fields if field.name not in ['user']]
    list_display.append('user_str')

    search_fields = ('id', 'user__email', 'preference')
    list_filter = [UserFilter, PreferenceFilter, WeightFilter]
    items_per_page = 25
    actions = [delete_all_users]

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserProfile._meta.fields if field.name not in ['user', 'image_url', 'job', 'solvedThreads']]
    list_display.append('user_str')
    list_display.append('job_str')
    list_display.append('image_url_str')
    list_display.append('solvedThreads_str')
    search_fields = ('id', 'user__email', 'bio', 'job__name')
    list_filter = [UserFilter, ImageUrlFilter, BioFilter, TokenFilter, JobFilter]
    items_per_page = 25

    actions = [delete_all_users]

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Tag._meta.fields]
    list_filter =  [NameFilter]
    search_fields = ('name', 'id')
    items_per_page = 25

    actions = [fill_data_with_tags]

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Thread._meta.fields if field.name not in ['main_tag', 'subtags', 'image_url', 'created_by']]
    list_display.append('main_tag_str')
    list_display.append('subtags_str')
    list_display.append('image_url_str')
    list_display.append('created_by_str')
    list_filter = [TitelFilter, ContentFilter, ContentSummaryFilter, MainTagFilter, ImageUrlFilter, CreatedByFilter, SubtagsFilter]
    search_fields = ('titel', 'content', 'created_by__username', 'id_thread')
    items_per_page = 25


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Comment._meta.fields if field.name not in ['thread', 'created_by', 'reacting']]
    list_display.append('thread_str')
    list_display.append('created_by_str')
    list_display.append('reacting_str')
    list_filter = [CreatedByFilter]
    search_fields = ('content', 'created_by__username', 'comment_id')
    items_per_page = 25

@admin.register(SharedQuestion)
class SharedQuestionAdmin(admin.ModelAdmin):
    list_display = [field.name for field in SharedQuestion._meta.fields if field.name not in ['thread', 'created_by']]
    list_display.append('thread_str')
    list_display.append('created_by_str')
    search_fields = ('content', 'created_by__username', 'shared_id', 'id')
    list_filter = [ThreadFilter, ContentFilter, CreatedByFilter, UpvotesFilter]
    items_per_page = 25

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserActivity._meta.fields if field.name not in ['user', 'upvoted_threads', 'downvoted_threads', 'upvoted_comments', 'downvoted_comments', 'upvoted_shared_questions', 'downvoted_shared_questions']]
    list_display.append('user_str')
    list_display.append('upvotedThreads_str')
    list_display.append('downvotedThreads_str')
    list_display.append('upvotedComments_str')
    list_display.append('downvotedComments_str')
    list_display.append('upvotedSharedQuestions_str')
    list_display.append('downvotedSharedQuestions_str')
    search_fields = ('user__username', 'id')
    list_filter = [UserFilter, UpvotedThreadsFilter, DownvotedThreadsFilter, UpvotedCommentsFilter, DownvotedCommentsFilter, UpvotedSharedQuestionsFilter, DownvotedSharedQuestionsFilter]
    items_per_page = 25

@admin.register(ReportModel)
class ReportModelAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ReportModel._meta.fields if field.name not in ['reported_by', 'reported_object']]
    list_display.append('reported_by_str')
    list_display.append('reported_object_str')
    # list_display.append('content_type_str')
    search_fields = ('reported_by__username', 'reported_why', 'reported_object', 'report_id', 'id')
    list_filter = [ReportedByFilter, ObjectIDFilter, ReportedTypeFilter, ReportedWhyFilter, ContentTypeFilter ]
    items_per_page = 25

@admin.register(SearchRequests)
class SearchRequestAdmin(admin.ModelAdmin):
    list_display = [field.name for field in SearchRequests._meta.fields if field.name not in ['user']]
    list_display.append('user_str')
    search_fields = ('search_id', 'user__username', 'timestamp', 'search_term')
    list_filter = [UserFilter, SearchTermFilter, searchResultFilter]
    items_per_page = 25

@admin.register(UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UploadedImage._meta.fields if field.name not in ['uploaded_by']]
    list_display.append('uploaded_by_str')
    search_fields = ('image_id', 'uploaded_by__username', 'uploaded_at')
    list_filter = [ImageFilter, UploadedAtFilter, UploadedByFilter]
    items_per_page = 25
    
@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = [field.name for field in CompanyProfile._meta.fields]
    search_fields = ('name', 'branche', 'interests', 'id')
    list_filter = [NameFilter, BrancheFilter, InterestsFilter]
    items_per_page = 25

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Job._meta.fields if field.name not in ['ImportantInformations']]
    list_display.append('ImportantInformations_str')
    search_fields = ('name', 'id')
    list_filter =  [NameFilter, ImportantInformationsFilter]
    items_per_page = 25

@admin.register(ImportantInformation)
class ImportantInformationAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ImportantInformation._meta.fields if field.name not in ['informationFrom']]
    list_display.append('informationFrom_str')
    search_fields = ('information', 'id')  
    list_filter = [InformationFilter, InformationFromFilter]
    items_per_page = 25

@admin.register(QuizAbsolved)
class QuizAbsolvedAdmin(admin.ModelAdmin):
    list_display = [field.name for field in QuizAbsolved._meta.fields]
    search_fields = ('id', 'Question', 'AnwerFromUser', 'AiAnswer', 'score')
    list_filter = [QuestionFilter, AnswerFromUser, AiAnswerFilter, ScoreFilter]
    items_per_page = 25

@admin.register(SolvedThreads)
class SolvedThreadsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in SolvedThreads._meta.fields if field.name not in ['Threads', 'QuizAbsolved']]
    list_display.append('threads_str')
    list_display.append('quiz_absolved_str')
    search_fields = ('id', 'threads', 'quiz_absolved')
    list_filter = [ThreadsFilter, QuizAbsolvedFilter]
    items_per_page = 25