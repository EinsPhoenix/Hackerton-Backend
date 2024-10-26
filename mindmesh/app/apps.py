from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.contrib.auth import get_user_model

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'  

    def ready(self):
        post_migrate.connect(create_super_user, sender=self)

def create_super_user(sender, **kwargs):
    create_superuser_if_not_exists()


def create_superuser_if_not_exists():
    User = get_user_model()  
    username = 'winder'
    email = 'winder@gmail.com'
    password = 'winder123'

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f'Superuser {username} wurde erstellt.')
    else:
        print(f'Superuser {username} existiert bereits.')
