# Standardbibliotheken
import logging

# Lokale Module
from ...models import (
    UserPreferences, 
)



logger = logging.getLogger(__name__)

def update_preferences(user_activity, thread, delta):
    main_tag = thread.main_tag
    
    try:
        preference = UserPreferences.objects.get(user=user_activity.user, preference=main_tag.name)
    except UserPreferences.DoesNotExist:
        print(main_tag.name)
        return

    if preference.weight < 100 and preference.weight > 0.1:
        preference.weight = min(100, preference.weight + delta)  
        preference.save()

    for subtag in thread.subtags.all():
        try:
            preference = UserPreferences.objects.get(user=user_activity.user, preference=subtag.name)
        except UserPreferences.DoesNotExist:
            return
        
        if preference.weight < 100 and preference.weight > 0.01:
            preference.weight = min(100, preference.weight + delta * 0.05)  
            preference.save()

def handle_thread_clicked(thread, user, delta):
    try:
        main_tag = thread.main_tag
        preference = UserPreferences.objects.get(user=user, preference=main_tag.name)
    except UserPreferences.DoesNotExist:
        return 404, {"succes":False, "message":"Userpreferences do not exist"}
    
    if preference.weight < 100 and preference.weight > 0.05:
        preference.weight = min(100, preference.weight )  
        preference.save()

    for subtag in thread.subtags.all():
        try:
            preference = UserPreferences.objects.get(user, preference=subtag.name)
        except UserPreferences.DoesNotExist:
            return 404, {"succes":False, "message":"Userpreferences do not exist"}
        
        if preference.weight < 100 and preference.weight > 0.01:
            preference.weight = min(100, preference.weight + delta * 0.01)  
            preference.save()
            
        return 201, {"succes":True, "message": "Weight was updated successfully"}
    

def handle_thread_vote(user_activity, thread, upvote_type):
    if upvote_type == "upvote":
        if thread in user_activity.downvotedThreads.all():
            user_activity.downvotedThreads.remove(thread)
            user_activity.upvotedThreads.add(thread)
            thread.upvotes += 2
            update_preferences(user_activity, thread, 0.05)
        elif thread not in user_activity.upvotedThreads.all():
            user_activity.upvotedThreads.add(thread)
            thread.upvotes += 1
            update_preferences(user_activity, thread, 0.05)
        elif thread in user_activity.upvotedThreads.all():
            user_activity.upvotedThreads.remove(thread)
            thread.upvotes -= 1
            update_preferences(user_activity, thread, -0.05)
    elif upvote_type == "downvote":
        if thread in user_activity.upvotedThreads.all():
            user_activity.upvotedThreads.remove(thread)
            user_activity.downvotedThreads.add(thread)
            thread.upvotes -= 2
            update_preferences(user_activity, thread, -0.05)
        elif thread not in user_activity.downvotedThreads.all():
            user_activity.downvotedThreads.add(thread)
            thread.upvotes -= 1
            update_preferences(user_activity, thread, -0.05)
        elif thread in user_activity.downvotedThreads.all():
            user_activity.downvotedThreads.remove(thread)
            thread.upvotes += 1
            update_preferences(user_activity, thread, 0.05)

    thread.save()
    user_activity.save()


def handle_comment_vote(user_activity, comment, upvote_type):
    if upvote_type == "upvote":
        if comment in user_activity.downvotedComments.all():
            user_activity.downvotedComments.remove(comment)
            user_activity.upvotedComments.add(comment)
            comment.upvotes += 2
        elif comment not in user_activity.upvotedComments.all():
            user_activity.upvotedComments.add(comment)
            comment.upvotes += 1
        elif comment in user_activity.upvotedComments.all():
            user_activity.upvotedComments.remove(comment)
            comment.upvotes -= 1
    elif upvote_type == "downvote":
        if comment in user_activity.upvotedComments.all():
            user_activity.upvotedComments.remove(comment)
            user_activity.downvotedComments.add(comment)
            comment.upvotes -= 2
        elif comment not in user_activity.downvotedComments.all():
            user_activity.downvotedComments.add(comment)
            comment.upvotes -= 1
        elif comment in user_activity.downvotedComments.all():
            user_activity.downvotedComments.remove(comment)
            comment.upvotes += 1

    comment.save() 
    user_activity.save() 


def handle_shared_vote(user_activity, shared, upvote_type):
    if upvote_type == "upvote":
        if shared in user_activity.downvotedSharedQuestions.all():
            user_activity.downvotedSharedQuestions.remove(shared)
            user_activity.upvotedSharedQuestions.add(shared)
            shared.upvotes += 2
        elif shared not in user_activity.upvotedSharedQuestions.all():
            user_activity.upvotedSharedQuestions.add(shared)
            shared.upvotes += 1
        elif shared in user_activity.upvotedSharedQuestions.all():
            user_activity.upvotedSharedQuestions.remove(shared)
            shared.upvotes -= 1
    elif upvote_type == "downvote":
        if shared in user_activity.upvotedSharedQuestions.all():
            user_activity.upvotedSharedQuestions.remove(shared)
            user_activity.downvotedSharedQuestions.add(shared)
            shared.upvotes -= 2
        elif shared not in user_activity.downvotedSharedQuestions.all():
            user_activity.downvotedSharedQuestions.add(shared)
            shared.upvotes -= 1
        elif shared in user_activity.downvotedSharedQuestions.all():
            user_activity.downvotedSharedQuestions.remove(shared)
            shared.upvotes += 1

    shared.save()
    user_activity.save()