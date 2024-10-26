from django.db import models


# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image_url = models.ForeignKey(UploadedImage, on_delete=models.CASCADE, null=True, blank=False)
    bio = models.TextField(blank=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=True, null=True)
    solvedThreads = models.ManyToManyField(SolvedThreads, blank=True, null=False)

    def __str__(self):
        return self.user.username


class QuizAbsolved(models.Model):
    Question = models.TextField(null=False)
    AnswerFromUser = models.TextField(blank=True, null=False)
    AiAnswer = models.TextField(blank=True, null=False)
    score = models.IntegerField(default=0)


class SolvedThreads(models.Model):
    Threads = models.ManyToManyField(Thread, blank=True, null=False)
    QuizAbsolved = models.ManyToManyField(QuizAbsolved, blank=True, null=False)
    Created_At = models.DateTimeField(auto_now_add=True)
