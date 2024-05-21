from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.db import connection


class PostgreSQLAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        with connection.cursor() as cursor:
            cursor.execute("SELECT validate_user(%s, %s, TRUE);", [username, password])
            result = cursor.fetchone()

        if result and result[0]:
            # User authentication succeeded, create or retrieve the user
            user, created = User.objects.get_or_create(username=username)
            return user
        else:
            # User authentication failed
            return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
