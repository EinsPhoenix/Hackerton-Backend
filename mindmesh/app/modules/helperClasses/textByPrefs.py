from django.utils import timezone

from ...models import Thread,  UserActivity, UserPreferences
import random

class TextsByPrefs:

    def __init__(self, user):
        self.user = user
        print(user)
        self.preferences = self.get_user_preferences()

    def get_user_preferences(self):
        preferences = UserPreferences.objects.filter(user=self.user)
        return {pref.preference: pref.weight for pref in preferences}

    def calculate_thread_weight(self, thread):
        weight = 0
        preferences = self.preferences

        main_tag_weight = preferences.get(thread.main_tag.name, 0)  
        weight += main_tag_weight

        print(f"{main_tag_weight} thread name: {thread.main_tag.name}")

        subtag_weight = sum(preferences.get(subtag.name, 0) * 0.5 for subtag in thread.subtags.all())
        weight += subtag_weight


        upvote_weight = thread.upvotes  
        weight += upvote_weight * 0.01  
        
        
        weight -= abs(upvote_weight) * 0.05  

        print(f"Upvote weight: {upvote_weight}, Total weight: {weight}")

        return weight

    def get_weighted_threads(self, num_threads=30):
        all_threads = Thread.objects.all()
        print(4)
        weighted_threads = []
        selected_thread_ids = set()

        print(3)
        user_activity = UserActivity.objects.filter(user=self.user).first()
        if user_activity:
            upvoted_threads = set(user_activity.upvotedThreads.values_list('id_thread', flat=True))
            downvoted_threads = set(user_activity.downvotedThreads.values_list('id_thread', flat=True))
        else:
            upvoted_threads = set()
            downvoted_threads = set()

        voted_thread_ids = upvoted_threads.union(downvoted_threads)

        for thread in all_threads:
            if thread.id_thread in voted_thread_ids:
                continue  

            print(f"Thread {thread}")
            thread_weight = self.calculate_thread_weight(thread)

            age_in_days = (timezone.now() - thread.created_at).days
            if age_in_days < 1: 
                thread_weight += 10  
            elif age_in_days < 7:  
                thread_weight += 5 

            print(f"Thread weight {thread_weight}")

            if thread.id_thread not in selected_thread_ids:  
                weighted_threads.extend([thread] * int(thread_weight))
                selected_thread_ids.add(thread.id_thread)  

        selected_threads = random.sample(weighted_threads, min(len(weighted_threads), num_threads))

        return selected_threads