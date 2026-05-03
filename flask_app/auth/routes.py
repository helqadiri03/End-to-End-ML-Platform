from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from .db_utils import get_db_cursor
from .password_utils import validate_password, hash_password, check_password

# Create a blueprint
auth = Blueprint('auth', __name__)

@auth.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate password match
        if password != confirm_password:
            flash("Passwords do not match.", 'error')
            return redirect(url_for('auth.register'))

        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('auth.register'))

        try:
            with get_db_cursor() as cursor:
                # Check if username already exists
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                existing_username = cursor.fetchone()
                
                # Check if email already exists
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                existing_email = cursor.fetchone()

                # If username or email already exists, flash an error
                if existing_username:
                    flash("Username already exists. Please choose a different username.", 'error')
                    return redirect(url_for('auth.register'))
                
                if existing_email:
                    flash("Email already in use. Please use a different email address.", 'error')
                    return redirect(url_for('auth.register'))

                # If no existing user, proceed with registration
                password_hash = hash_password(password)
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, password_hash)
                )
            
            flash("Registration successful. Please log in.", 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            flash(f"Error during registration: {str(e)}", 'error')
            return redirect(url_for('auth.register'))

    return render_template('register.html')

@auth.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_user_by_username(username)

        if user:
            print(f"User found: {user.username}")
        else:
            print("User not found.")

        if user and check_password(user.password_hash, password):
            print("Password verified successfully.")
            login_user(user)
            flash("Login successful!", 'success')
            return redirect(url_for('analyse'))
        else:
            print("Invalid credentials.")
            flash("Invalid username or password.", 'error')

    return render_template('login.html')



@auth.route('/auth/logout')
def logout():
    logout_user()
    flash("You have been logged out.", 'info')
    return redirect(url_for('index'))