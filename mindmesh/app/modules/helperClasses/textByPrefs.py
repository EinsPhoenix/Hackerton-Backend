import random
from ...models import Thread, UserPreferences

class TextsByPrefs:
    def __init__(self, user):
        self.user = user
        self.preferences = self.get_user_preferences()

    def get_user_preferences(self):
        # Retrieve user preferences with weight filtering
        preferences = UserPreferences.objects.filter(user=self.user, weight__gt=25).values("preference", "weight")
        return {pref["preference"]: pref["weight"] for pref in preferences}

    def get_weighted_threads(self, num_threads=20):
        # Fetch preferred tags based on user preferences
        preferred_tags = list(self.preferences.keys())

        if not preferred_tags:
            # If there are no preferred tags, return an empty list or handle accordingly
            return []

        # Fetch all relevant threads matching the user's preferred tags
        relevant_threads = (
            Thread.objects
            .filter(main_tag__name__in=preferred_tags)
        )

        # Randomly select a number of threads from the relevant ones
        total_relevant_threads = relevant_threads.count()

        # If there are fewer relevant threads than requested, adjust num_threads
        num_threads = min(num_threads, total_relevant_threads)

        # Randomly sample threads from the relevant ones
        selected_threads = random.sample(list(relevant_threads), num_threads)

        return selected_threads
