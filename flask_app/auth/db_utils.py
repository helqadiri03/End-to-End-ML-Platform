import psycopg2
from contextlib import contextmanager

DB_CONFIG = {
    'dbname': 'defaultdb',
    'user': 'avnadmin',
    'password': 'YOUR_DATABASE_PASSWORD',
    'host': 'pg-387b88b6-lbtata900-ec9a.e.aivencloud.com', 
    'port': '26404',
    'sslmode': 'require'
}

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    finally:
        if conn is not None:
            conn.close()

@contextmanager
def get_db_cursor():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        yield cursor
        conn.commit() 