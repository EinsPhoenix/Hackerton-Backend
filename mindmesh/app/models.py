from django.contrib.auth.models import AbstractUser, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import mark_safe
import os
from .modules.aiModule import GenerateResponse
from django.utils import timezone


class CompanyProfile(models.Model):
    name = models.TextField()
    interests = models.TextField()
    branche = models.TextField()
    
    class Meta:
        ordering = ['name']
    
    
class UserPreferences(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    preference = models.CharField(max_length=255)
    weight = models.FloatField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.user.username}'s preference"
    
    def user_str(self):
        returnString = ""
        user = self.user

        if user:
            link = reverse("admin:%s_%s_change" % (user._meta.app_label, user._meta.model_name), args=[user.pk])
            returnString = f'<a href="{link}">{user.username}</a>'
        return mark_safe(returnString)
    
    user_str.short_description = 'User'
    user_str.admin_order_field = 'user'
    

    
class UploadedImage(models.Model):
    image_id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to='images/')  
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE) 

    class Meta:
        ordering = ['image_id']


    def __str__(self):
        return self.image.name
    
    def uploaded_by_str(self):
        returnString = ""
        user = self.uploaded_by

        if user:
            link = reverse("admin:%s_%s_change" % (user._meta.app_label, user._meta.model_name), args=[user.pk])
            returnString = f'<a href="{link}">{user.username}</a>'
        return mark_safe(returnString)
    
    uploaded_by_str.short_description = 'Uploaded by'
    uploaded_by_str.admin_order_field = 'uploaded_by'

class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True) 

    def __str__(self):
        return self.name


    
class Thread(models.Model):
    id_thread = models.AutoField(primary_key=True)
    titel = models.TextField()
    content = models.TextField()
    content_summary = models.TextField()  
    main_tag = models.ForeignKey(Tag, related_name='main_threads', on_delete=models.CASCADE)
    subtags = models.ManyToManyField(Tag, related_name='sub_threads', blank=True)
    image_url = models.ForeignKey(UploadedImage, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    upvotes = models.IntegerField(default=0)

    class Meta:
        ordering = ['id_thread']
    
    def __str__(self):
        return self.content[:50]  
    
    def main_tag_str(self):
        returnString = ""
        tag = self.main_tag

        if tag:
            link = reverse("admin:%s_%s_change" % (tag._meta.app_label, tag._meta.model_name), args=[tag.pk])
            returnString = f'<a href="{link}">{tag.name}</a>'
        return mark_safe(returnString)
    
    def image_url_str(self):
        returnString = ""
        image = self.image_url

        if image:
            link = reverse("admin:%s_%s_change" % (image._meta.app_label, image._meta.model_name), args=[image.pk])
            returnString = f'<a href="{link}">{image.image.name}</a>'
        return mark_safe(returnString)
    
    def created_by_str(self):
        returnString = ""
        user = self.created_by

        if user:
            link = reverse("admin:%s_%s_change" % (user._meta.app_label, user._meta.model_name), args=[user.pk])
            returnString = f'<a href="{link}">{user.username}</a>'
        return mark_safe(returnString)
    
    def subtags_str(self):
        returnString = ""
        tags = self.subtags.all()

        for tag in tags:
            link = reverse("admin:%s_%s_change" % (tag._meta.app_label, tag._meta.model_name), args=[tag.pk])
            returnString += f'<a href="{link}">{tag.name}</a><br>'
        return mark_safe(returnString)
    
    main_tag_str.short_description = 'Main Tag'
    main_tag_str.admin_order_field = 'main_tag'

    subtags_str.short_description = 'Subtags'
    subtags_str.admin_order_field = 'subtags'

    image_url_str.short_description = 'Image URL'
    image_url_str.admin_order_field = 'image_url'

    created_by_str.short_description = 'Created by'
    created_by_str.admin_order_field = 'created_by'

    
    def save(self, *args, **kwargs):
        if self.pk is not None:
           
            existing_thread = Thread.objects.get(pk=self.pk)
        
            if existing_thread.content == self.content:
                super().save(*args, **kwargs)  
                return
        

        super().save(*args, **kwargs) 
        print(f"Saved {self.pk}")

      
        if self.content:
            try:
                ImportantInformation.objects.filter(informationFrom=self).delete()
                company_profile = CompanyProfile.objects.first()  
                if company_profile:
                    response_generator = GenerateResponse()  
                    extracted_info = response_generator.extract_important_info(
                        company_profile.interests,
                        self.content,
                        Job.objects.values_list('name', flat=True)
                    )

                    if 'error' not in extracted_info:
                        job_name = extracted_info.get("job", None)
                        important_infos = extracted_info.get("importantInformation", [])

                        for info in important_infos:
                            important_info_obj = ImportantInformation.objects.create(
                                information=info['info'], 
                                informationFrom=self
                            )
                            if job_name:
                                job_group = Job.objects.filter(name=job_name).first()
                                if job_group:
                                    job_group.ImportantInformations.add(important_info_obj)
            except CompanyProfile.DoesNotExist:
                print("Error: unknown company profile")
            except Exception as e:
                print(f"An error occurred during processing: {e}")

class ImportantInformation(models.Model):
    information = models.TextField()
    informationFrom = models.ForeignKey(Thread, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.information[:50]} from {self.informationFrom.titel}"

    def informationFrom_str(self):
        returnString = ""
        thread = self.informationFrom

        if thread:
            link = reverse("admin:%s_%s_change" % (thread._meta.app_label, thread._meta.model_name), args=[thread.pk])
            returnString = f'<a href="{link}">{thread.titel}</a>'
        return mark_safe(returnString)
    
    informationFrom_str.short_description = 'Information from'
    informationFrom_str.admin_order_field = 'informationFrom'

class Job(models.Model):
    name = models.TextField()
    ImportantInformations = models.ManyToManyField(ImportantInformation, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def ImportantInformations_str(self):
        returnString = ""
        important_info = self.ImportantInformations.all()

        for info in important_info:
            link = reverse("admin:%s_%s_change" % (info._meta.app_label, info._meta.model_name), args=[info.pk])
            returnString += f'<a href="{link}">{str(info)}</a><br>'
        return mark_safe(returnString)
    
    ImportantInformations_str.short_description = 'Important Informations'
    ImportantInformations_str.admin_order_field = 'ImportantInformations'

class QuizAbsolved(models.Model):
    Question = models.TextField(null=False)
    AnswerFromUser = models.TextField(blank=True, null=False)
    AiAnswer = models.TextField(blank=True, null=False)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.Question[:50]} | {self.AnswerFromUser[:50]} | {self.AiAnswer[:50]}"
    

class SolvedThreads(models.Model):
    #TODO hier nahezu keine String repräsentation möglich 
    Threads = models.ManyToManyField(Thread, blank=True, null=False)
    QuizAbsolved = models.ManyToManyField(QuizAbsolved, blank=True, null=False)
    Created_At = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def threads_str(self):
        returnString = ""
        threads = self.Threads.all()

        for thread in threads:
            link = reverse("admin:%s_%s_change" % (thread._meta.app_label, thread._meta.model_name), args=[thread.pk])
            returnString += f'<a href="{link}">{thread.titel}</a><br>'
        return mark_safe(returnString)

    def quiz_absolved_str(self):
        returnString = ""
        quiz_absolved = self.QuizAbsolved.all()

        for quiz in quiz_absolved:
            link = reverse("admin:%s_%s_change" % (quiz._meta.app_label, quiz._meta.model_name), args=[quiz.pk])
            returnString += f'<a href="{link}">{str(quiz)}</a><br>'
        return mark_safe(returnString)
    
    threads_str.short_description = 'Threads'
    threads_str.admin_order_field = 'Threads'

    quiz_absolved_str.short_description = 'Quiz Absolved'
    quiz_absolved_str.admin_order_field = 'QuizAbsolved'
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image_url = models.ForeignKey(UploadedImage, on_delete=models.CASCADE, null=True, blank=False)
    bio = models.TextField(blank=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=True, null=True)
    solvedThreads = models.ManyToManyField(SolvedThreads, blank=True, null=False)

    def __str__(self):
        return self.user.username
    
    def user_str(self):
        returnString = ""
        user = self.user

        if user:
            link = reverse("admin:%s_%s_change" % (user._meta.app_label, user._meta.model_name), args=[user.pk])
            returnString = f'<a href="{link}">{user.username}</a>'
        return mark_safe(returnString)
    
    def image_url_str(self):
        returnString = ""
        image = self.image_url

        if image:
            link = reverse("admin:%s_%s_change" % (image._meta.app_label, image._meta.model_name), args=[image.pk])
            returnString = f'<a href="{link}">{image.image.name}</a>'
        return mark_safe(returnString)
    
    def job_str(self):
        returnString = ""
        job = self.job

        if job:
            link = reverse("admin:%s_%s_change" % (job._meta.app_label, job._meta.model_name), args=[job.pk])
            returnString = f'<a href="{link}">{job.name}</a>'
        return mark_safe(returnString)
    
    def solvedThreads_str(self):
        returnString = ""
        solved_threads = self.solvedThreads.all()

        for thread in solved_threads:
            link = reverse("admin:%s_%s_change" % (thread._meta.app_label, thread._meta.model_name), args=[thread.pk])
            returnString += f'<a href="{link}">{thread.id}</a><br>'
        return mark_safe(returnString)
    
    user_str.short_description = 'User'
    user_str.admin_order_field = 'user'

    image_url_str.short_description = 'Image URL'
    image_url_str.admin_order_field = 'image_url'

    job_str.short_description = 'Job'
    job_str.admin_order_field = 'job'

    solvedThreads_str.short_description = 'Solved Threads'
    solvedThreads_str.admin_order_field = 'solvedThreads'

class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    thread = models.ForeignKey(Thread, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    upvotes = models.IntegerField(default=0)
    reacting = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

    class Meta:
        ordering = ['comment_id']

    def __str__(self):
        return self.content[:50]
    
    def thread_str(self):
        returnString = ""
        thread = self.thread

        if thread:
            link = reverse("admin:%s_%s_change" % (thread._meta.app_label, thread._meta.model_name), args=[thread.pk])
            returnString = f'<a href="{link}">{thread.titel}</a>'
        return mark_safe(returnString)
    
    def created_by_str(self):
        returnString = ""
        user = self.created_by

        if user:
            link = reverse("admin:%s_%s_change" % (user._meta.app_label, user._meta.model_name), args=[user.pk])
            returnString = f'<a href="{link}">{user.username}</a>'
        return mark_safe(returnString)
    
    def reacting_str(self):
        returnString = ""
        comment = self.reacting

        if comment:
            link = reverse("admin:%s_%s_change" % (comment._meta.app_label, comment._meta.model_name), args=[comment.pk])
            returnString = f'<a href="{link}">{comment.content}</a>'
        return mark_safe(returnString)
    
    thread_str.short_description = 'Thread'
    thread_str.admin_order_field = 'thread'

    created_by_str.short_description = 'Created by'
    created_by_str.admin_order_field = 'created_by'

    reacting_str.short_description = 'Reacting'
    reacting_str.admin_order_field = 'reacting'


class SharedQuestion(models.Model):
    shared_id = models.AutoField(primary_key=True)
    thread = models.ForeignKey(Thread, related_name='shared_questions', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    upvotes = models.IntegerField(default=0)  

    class Meta:
        ordering = ['shared_id']

    def __str__(self):
        return self.content[:50]
    
    def thread_str(self):
        returnString = ""
        thread = self.thread

        if thread:
            link = reverse("admin:%s_%s_change" % (thread._meta.app_label, thread._meta.model_name), args=[thread.pk])
            returnString = f'<a href="{link}">{thread.titel}</a>'
        return mark_safe(returnString)
    
    def created_by_str(self):
        returnString = ""
        user = self.created_by

        if user:
            link = reverse("admin:%s_%s_change" % (user._meta.app_label, user._meta.model_name), args=[user.pk])
            returnString = f'<a href="{link}">{user.username}</a>'
        return mark_safe(returnString)
    
    thread_str.short_description = 'Thread'
    thread_str.admin_order_field = 'thread'

    created_by_str.short_description = 'Created by'
    created_by_str.admin_order_field = 'created_by'
    
class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    upvotedThreads = models.ManyToManyField(Thread, related_name='threadsUpvoted')
    downvotedThreads = models.ManyToManyField(Thread, related_name='threadsDownvoted')
    upvotedComments = models.ManyToManyField(Comment, related_name='upvotedComments')
    downvotedComments = models.ManyToManyField(Comment, related_name='downvotedComments')
    upvotedSharedQuestions = models.ManyToManyField(SharedQuestion, related_name='upvotedSharedQuestions')
    downvotedSharedQuestions = models.ManyToManyField(SharedQuestion, related_name='downvotedSharedQuestions')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"UserActivity for {self.user.username}: Upvoted Threads (count: {self.upvotedThreads.count()})"

    def user_str(self):
        returnString = ""
        user = self.user

        if user:
            link = reverse("admin:%s_%s_change" % (user._meta.app_label, user._meta.model_name), args=[user.pk])
            returnString = f'<a href="{link}">{user.username}</a>'
        return mark_safe(returnString)
    
    def upvotedThreads_str(self):
        returnString = ""
        threads = self.upvotedThreads.all()

        for thread in threads:
            link = reverse("admin:%s_%s_change" % (thread._meta.app_label, thread._meta.model_name), args=[thread.pk])
            returnString += f'<a href="{link}">{thread.titel}</a><br>'
        return mark_safe(returnString)
    
    def downvotedThreads_str(self):
        returnString = ""
        threads = self.downvotedThreads.all()

        for thread in threads:
            link = reverse("admin:%s_%s_change" % (thread._meta.app_label, thread._meta.model_name), args=[thread.pk])
            returnString += f'<a href="{link}">{thread.titel}</a><br>'
        return mark_safe(returnString)
    
    def upvotedComments_str(self):
        returnString = ""
        comments = self.upvotedComments.all()

        for comment in comments:
            link = reverse("admin:%s_%s_change" % (comment._meta.app_label, comment._meta.model_name), args=[comment.pk])
            returnString += f'<a href="{link}">{comment.content}</a><br>'
        return mark_safe(returnString)
    
    def downvotedComments_str(self):
        returnString = ""
        comments = self.downvotedComments.all()

        for comment in comments:
            link = reverse("admin:%s_%s_change" % (comment._meta.app_label, comment._meta.model_name), args=[comment.pk])
            returnString += f'<a href="{link}">{comment.content}</a><br>'
        return mark_safe(returnString)
    
    def upvotedSharedQuestions_str(self):
        returnString = ""
        shared_questions = self.upvotedSharedQuestions.all()

        for shared_question in shared_questions:
            link = reverse("admin:%s_%s_change" % (shared_question._meta.app_label, shared_question._meta.model_name), args=[shared_question.pk])
            returnString += f'<a href="{link}">{shared_question.content}</a><br>'
        return mark_safe(returnString)
    
    def downvotedSharedQuestions_str(self):
        returnString = ""
        shared_questions = self.downvotedSharedQuestions.all()

        for shared_question in shared_questions:
            link = reverse("admin:%s_%s_change" % (shared_question._meta.app_label, shared_question._meta.model_name), args=[shared_question.pk])
            returnString += f'<a href="{link}">{shared_question.content}</a><br>'
        return mark_safe(returnString)
    
    user_str.short_description = 'User'
    user_str.admin_order_field = 'user'

    upvotedThreads_str.short_description = 'Upvoted Threads'
    upvotedThreads_str.admin_order_field = 'upvotedThreads'

    downvotedThreads_str.short_description = 'Downvoted Threads'
    downvotedThreads_str.admin_order_field = 'downvotedThreads'

    upvotedComments_str.short_description = 'Upvoted Comments'
    upvotedComments_str.admin_order_field = 'upvotedComments'

    downvotedComments_str.short_description = 'Downvoted Comments'
    downvotedComments_str.admin_order_field = 'downvotedComments'

    upvotedSharedQuestions_str.short_description = 'Upvoted Shared Questions'
    upvotedSharedQuestions_str.admin_order_field = 'upvotedSharedQuestions'

    downvotedSharedQuestions_str.short_description = 'Downvoted Shared Questions'
    downvotedSharedQuestions_str.admin_order_field = 'downvotedSharedQuestions'





class ReportModel(models.Model):
    report_id = models.AutoField(primary_key=True)
    reported_by = models.ForeignKey(User, related_name='reports', on_delete=models.CASCADE)
    reported_at = models.DateTimeField(auto_now_add=True)
    reported_why = models.TextField()

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    reported_object = GenericForeignKey('content_type', 'object_id')

    REPORT_CHOICES = [
        ('thread', 'Thread'),
        ('comment', 'Comment'),
        ('question', 'SharedQuestion'),
    ]
    reported_type = models.CharField(max_length=50, choices=REPORT_CHOICES)

    class Meta:
        ordering = ['report_id']

    def __str__(self):
        return f"Report {self.report_id} by {self.reported_by.username}"
    
    def reported_by_str(self):
        returnString = ""
        user = self.reported_by

        if user:
            link = reverse("admin:%s_%s_change" % (user._meta.app_label, user._meta.model_name), args=[user.pk])
            returnString = f'<a href="{link}">{user.username}</a>'
        return mark_safe(returnString)
    
    # def content_type_str(self):
    #     returnString = ""
    #     content_type = self.content_type

    #     if content_type:
    #         link = reverse("admin:%s_%s_change" % (content_type._meta.app_label, content_type._meta.model_name), args=[content_type.pk])
    #         returnString = f'<a href="{link}">{content_type.model}</a>'
    #     return mark_safe(returnString)
    
    def reported_object_str(self):
        returnString = ""
        obj = self.reported_object

        if obj:
            link = reverse("admin:%s_%s_change" % (obj._meta.app_label, obj._meta.model_name), args=[obj.pk])
            returnString = f'<a href="{link}">{obj}</a>'
        return mark_safe(returnString)
    
    reported_by_str.short_description = 'Reported by'
    reported_by_str.admin_order_field = 'reported_by'

    # content_type_str.short_description = 'Content Type'
    # content_type_str.admin_order_field = 'content_type'

    reported_object_str.short_description = 'Reported Object'
    reported_object_str.admin_order_field = 'reported_object'
    

class SearchRequests(models.Model):
    search_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_term = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    search_result = models.JSONField(default=dict)

    class Meta:
        ordering = ['search_id']
    
    def __str__(self):
        return f"Report {self.search_id} by {self.user.username}"
    
    def user_str(self):
        returnString = ""
        user = self.user

        if user:
            link = reverse("admin:%s_%s_change" % (user._meta.app_label, user._meta.model_name), args=[user.pk])
            returnString = f'<a href="{link}">{user.username}</a>'
        return mark_safe(returnString)
    
    user_str.short_description = 'User'
    user_str.admin_order_field = 'user'

@receiver(post_delete, sender=UploadedImage)
def delete_image_file(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path):
        os.remove(instance.image.path)
        

@receiver(post_delete, sender=Thread)
def delete_important_info_from_thread(sender, instance, **kwargs):
    ImportantInformation.objects.filter(informationFrom=instance).delete()

@receiver(post_delete, sender=Job)
def delete_important_info_from_job(sender, instance, **kwargs):
    
    instance.ImportantInformations.clear() 
    ImportantInformation.objects.filter(id__in=instance.ImportantInformations.values()).delete()



