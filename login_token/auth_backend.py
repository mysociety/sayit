from django.contrib.auth.models import User

from .models import LoginToken, clean_token

class LoginTokenBackend(object):
    supports_inactive_user = True

    def authenticate(self, token=None):
        if token is None:
            return None
        try:
            token = clean_token(token)
            lt = LoginToken.objects.get(token=token)
        except LoginToken.DoesNotExist:
            return None
        return lt.user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
