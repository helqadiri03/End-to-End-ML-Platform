from flask_login import LoginManager
from .models import User
from .db_utils import get_db_cursor

def create_tables():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL
                )
            """)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")

def init_login_manager(app):
    create_tables()
    
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT id, username, email, password_hash FROM users WHERE id = %s", (user_id,))
                user_data = cursor.fetchone()
                return User(*user_data) if user_data else None
        except Exception as e:
            print(f"Error loading user: {e}")
            return None