from django.contrib import admin
from django.contrib.auth.models import User
from django.db import transaction
from .models import UserPreferences, UserProfile, Tag, Thread, Comment, SharedQuestion, UserActivity, ReportModel, SearchRequests, UploadedImage, CompanyProfile, Job, ImportantInformation
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
    list_filter = ('weight', 'preference')
    actions = [delete_all_users]

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserProfile._meta.fields if field.name not in ['user', 'image_url', 'job', 'solvedThreads']]
    list_display.append('user_str')
    list_display.append('job_str')
    list_display.append('image_url_str')
    list_display.append('solvedThreads_str')
    search_fields = ('id', 'user__email', 'bio', 'job__name')
    list_filter = ('user__email','job__name', 'id')
    actions = [delete_all_users]

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Tag._meta.fields]
    search_fields = ('name', 'id')
    actions = [fill_data_with_tags]

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Thread._meta.fields if field.name not in ['main_tag', 'subtags', 'image_url', 'created_by']]
    list_display.append('main_tag_str')
    list_display.append('subtags_str')
    list_display.append('image_url_str')
    list_display.append('created_by_str')


    search_fields = ('titel', 'content', 'created_by__username', 'id_thread')
    list_filter = ('main_tag', 'created_by', 'created_at', 'id_thread', 'image_url')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Comment._meta.fields if field.name not in ['thread', 'created_by', 'reacting']]
    list_display.append('thread_str')
    list_display.append('created_by_str')
    list_display.append('reacting_str')
    search_fields = ('content', 'created_by__username', 'comment_id', 'id')
    list_filter = ('thread', 'created_by', 'created_at', 'comment_id')

@admin.register(SharedQuestion)
class SharedQuestionAdmin(admin.ModelAdmin):
    list_display = [field.name for field in SharedQuestion._meta.fields if field.name not in ['thread', 'created_by']]
    list_display.append('thread_str')
    list_display.append('created_by_str')
    search_fields = ('content', 'created_by__username', 'shared_id', 'id')
    list_filter = ('thread', 'created_by', 'created_at', 'shared_id')

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

@admin.register(ReportModel)
class ReportModelAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ReportModel._meta.fields if field.name not in ['reported_by', 'reported_object']]
    list_display.append('reported_by_str')
    list_display.append('reported_object_str')
    # list_display.append('content_type_str')
    search_fields = ('reported_by__username', 'reported_why', 'reported_object', 'report_id', 'id')
    list_filter = ('reported_type', 'reported_at', 'reported_by')

@admin.register(SearchRequests)
class SearchRequestAdmin(admin.ModelAdmin):
    list_display = [field.name for field in SearchRequests._meta.fields if field.name not in ['user']]
    list_display.append('user_str')
    search_fields = ('search_id', 'user__username', 'timestamp', 'search_term')
    list_filter = ('search_id', 'user', 'timestamp')

@admin.register(UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UploadedImage._meta.fields if field.name not in ['uploaded_by']]
    list_display.append('uploaded_by_str')
    search_fields = ('image_id', 'uploaded_by__username', 'uploaded_at')
    list_filter = ('image_id', 'uploaded_by', 'uploaded_at')
    
@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = [field.name for field in CompanyProfile._meta.fields]
    search_fields = ('name', 'branche', 'interests', 'id')
    list_filter = ('name', 'branche', 'interests', 'id')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Job._meta.fields if field.name not in ['ImportantInformations']]
    list_display.append('ImportantInformations_str')
    search_fields = ('name', 'id')
    list_filter = ('name', 'id')

@admin.register(ImportantInformation)
class ImportantInformationAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ImportantInformation._meta.fields if field.name not in ['informationFrom']]
    list_display.append('informationFrom_str')
    search_fields = ('information', 'id')  
    list_filter = ('informationFrom', 'id')