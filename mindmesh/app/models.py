from django.contrib.auth.models import AbstractUser, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
from .modules.aiModule import GenerateResponse
from django.utils import timezone

class CompanyProfile(models.Model):
    name = models.TextField()
    interests = models.TextField()
    branche = models.TextField()
    
    
    
class UserPreferences(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    preference = models.CharField(max_length=255)
    weight = models.FloatField()

    def __str__(self):
        return f"{self.user.username}'s preference"
class UploadedImage(models.Model):
    image_id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to='images/')  
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE) 

    def __str__(self):
        return self.image.name

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
    
    def __str__(self):
        return self.content[:50]  

    
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

class Job(models.Model):
    name = models.TextField()
    ImportantInformations = models.ManyToManyField(ImportantInformation, blank=True)

class QuizAbsolved(models.Model):
    Question = models.TextField(null=False)
    AnswerFromUser = models.TextField(blank=True, null=False)
    AiAnswer = models.TextField(blank=True, null=False)
    score = models.IntegerField(default=0)
    

class SolvedThreads(models.Model):
    Threads = models.ManyToManyField(Thread, blank=True, null=False)
    QuizAbsolved = models.ManyToManyField(QuizAbsolved, blank=True, null=False)
    Created_At = models.DateTimeField(auto_now_add=True)
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image_url = models.ForeignKey(UploadedImage, on_delete=models.CASCADE, null=True, blank=False)
    bio = models.TextField(blank=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=True, null=True)
    solvedThreads = models.ManyToManyField(SolvedThreads, blank=True, null=False)

    def __str__(self):
        return self.user.username

class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    thread = models.ForeignKey(Thread, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    upvotes = models.IntegerField(default=0)
    reacting = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

    def __str__(self):
        return self.content[:50]


class SharedQuestion(models.Model):
    shared_id = models.AutoField(primary_key=True)
    thread = models.ForeignKey(Thread, related_name='shared_questions', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    upvotes = models.IntegerField(default=0)  

    def __str__(self):
        return self.content[:50]
    
class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    upvotedThreads = models.ManyToManyField(Thread, related_name='threadsUpvoted')
    downvotedThreads = models.ManyToManyField(Thread, related_name='threadsDownvoted')
    upvotedComments = models.ManyToManyField(Comment, related_name='upvotedComments')
    downvotedComments = models.ManyToManyField(Comment, related_name='downvotedComments')
    upvotedSharedQuestions = models.ManyToManyField(SharedQuestion, related_name='upvotedSharedQuestions')
    downvotedSharedQuestions = models.ManyToManyField(SharedQuestion, related_name='downvotedSharedQuestions')


    def __str__(self):
        return f"UserActivity for {self.user.username}: Upvoted Threads (count: {self.upvotedThreads.count()})"





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

    def __str__(self):
        return f"Report {self.report_id} by {self.reported_by.username}"
    

class SearchRequests(models.Model):
    search_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_term = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    search_result = models.JSONField(default=dict)
    
    def __str__(self):
        return f"Report {self.search_id} by {self.user.username}"

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



