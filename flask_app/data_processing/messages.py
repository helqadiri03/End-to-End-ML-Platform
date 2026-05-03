import psycopg2
from flask import request, render_template, redirect, url_for, flash



DB_CONFIG = {
    'dbname': 'defaultdb',
    'user': 'avnadmin',
    'password': 'YOUR_DATABASE_PASSWORD',
    'host': 'pg-387b88b6-lbtata900-ec9a.e.aivencloud.com', 
    'port': '26404',
    'sslmode': 'require'
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def index_route():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        # Créer la table si elle n'existe pas
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'messages')")
        if not cursor.fetchone()[0]:
            cursor.execute("CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, name VARCHAR(255), email VARCHAR(255), subject VARCHAR(255), message TEXT)")
            conn.commit()

        # Enregistrer le message dans la base de données
        cursor.execute(
            "INSERT INTO messages (name, email, subject, message) VALUES (%s, %s, %s, %s)",
            (name, email, subject, message)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Thank you! Your message has been sent successfully.')
        return redirect(url_for('index'))

    return render_template('index.html')

def messages_route():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, subject, message FROM messages")
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('messages.html', messages=messages)