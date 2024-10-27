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
        selected_tags = random.sample(preferred_tags, min(20, len(preferred_tags)))

       
        relevant_threads = (
            Thread.objects
            .filter(main_tag__name__in=selected_tags)
            .distinct()
            [:num_threads]
        )
        
        return list(relevant_threads)
