import random
from ...models import Thread, UserPreferences

class TextsByPrefs:
    def __init__(self, user):
        self.user = user
        self.preferences = self.get_user_preferences()

    def get_user_preferences(self):
        preferences = UserPreferences.objects.filter(user=self.user, weight__gt=25).values("preference", "weight")
        return {pref["preference"]: pref["weight"] for pref in preferences}

    def get_weighted_threads(self, num_threads=20):
        preferred_tags = list(self.preferences.keys())

        if not preferred_tags:
            return []

        relevant_threads = (
            Thread.objects
            .filter(main_tag__name__in=preferred_tags)
        )

   
        total_relevant_threads = relevant_threads.count()

        num_threads = min(num_threads, total_relevant_threads)

   
        selected_threads = random.sample(list(relevant_threads), num_threads)

        return selected_threads
