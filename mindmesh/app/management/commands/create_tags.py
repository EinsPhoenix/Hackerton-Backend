from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from ...models import Tag  

class Command(BaseCommand):
    help = 'Erstellt Standard-Tags in der Datenbank'

    def handle(self, *args, **kwargs):
        tags = [
            "Technology", "Science", "Music", "Culture", "Sports",
            "Movies and Series", "Education", "Literature", "History",
            "Travel", "Nature and Environment", "Fashion", "Culinary",
            "Psychology", "Finance", "Space Exploration", "Gaming",
            "Creativity and Design", "Art"
        ]

        try:
            for tag_name in tags:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Tag "{tag_name}" wurde erstellt.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Tag "{tag_name}" existiert bereits.'))
        except OperationalError:
            self.stdout.write(self.style.ERROR("Die Datenbank ist möglicherweise nicht bereit. Die Tags konnten nicht erstellt werden."))
