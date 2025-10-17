from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Check if username contains @ (email)
        if "@" in username:
            try:
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                return None
            except User.MultipleObjectsReturned:
                return None
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password):
            return user
        return None
