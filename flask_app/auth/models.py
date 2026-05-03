from flask_login import UserMixin
from .db_utils import get_db_cursor

class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    @staticmethod
    def get_user_by_username(username):
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            return User(*user_data) if user_data else None