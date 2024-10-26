# Standardbibliotheken
import logging
import os
import requests

# Django-Bibliotheken
from django.contrib.auth.hashers import make_password


# Google Auth-Bibliotheken
from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Drittanbieter-Bibliotheken
from fastapi import HTTPException

# Lokale Module
from ...models import (
    
    User,
    UserProfile,
    UserPreferences,
)
from ..helperClasses.userActivitys import (
    create_custom_token,
)


logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class TokenVerificationHelper:
    @staticmethod
    def verify_and_create_user(payload):
        try:
            device_type_to_env = {
                "android": "GOOGLE_CLIENT_ID_ANDROID",
                "ios": "GOOGLE_CLIENT_ID_IOS",
                "web": "GOOGLE_CLIENT_ID_WEB",
            }

            client_key = os.getenv(device_type_to_env.get(payload.devicetype))
            if client_key is None:
                raise ValueError("Invalid Device_Type or not found in environment variables")

            access_token = payload.token

            response = requests.get(f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}")
            logger.warning(f"0{response}")

            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Access Token is invalid")

            token_info = response.json()
            logger.warning(f"1{token_info}")

            profile_response = requests.get(
                f"https://people.googleapis.com/v1/people/me?personFields=names,emailAddresses",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            logger.warning(f": {profile_response}")

            if profile_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Unable to retrieve user profile")

            profile_info = profile_response.json()
            logger.warning(f"Profile Info: {profile_info}")

            name = profile_info.get('names', [{}])[0].get('displayName', 'User')
            email = profile_info.get('emailAddresses', [{}])[0].get('value', '')

            user, created = User.objects.get_or_create(
                username=name,
                email=email,
                defaults={'password': make_password(token_info['sub'])}
            )

            custom_token = create_custom_token(user.id, user.username, user.email)

            user_profile, _ = UserProfile.objects.get_or_create(user=user)
            user_profile.token = custom_token
            user_profile.save()

            preferences_list = []
            user_preferences = UserPreferences.objects.filter(user=user)
            if user_preferences.exists():
                preferences_list = [preference.preference for preference in user_preferences]

            return {
                "success": True,
                "token": custom_token,
                "created": created,
                "preferences": preferences_list
            }

        except Exception as e:
            logger.error(f"Error occurred while verifying token: {e}")
            return 404, {"success": False, "message": str(e)}