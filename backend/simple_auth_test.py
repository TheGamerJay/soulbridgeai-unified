#!/usr/bin/env python3
"""
Simple Flask app to test authentication forms
"""
import os
import sys
import tempfile
from flask import Flask, render_template, request, flash, redirect, url_for, session

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import SoulBridge models
from models import SoulBridgeDB

app = Flask(__name__)
app.secret_key = "test-secret-key"

# Initialize test database
db = SoulBridgeDB()

@app.route("/")
def home():
    return '<h1>SoulBridge Auth Test</h1><p><a href="/login">Login</a> | <a href="/register">Register</a></p>'

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register") 
def register():
    return render_template("register.html")

@app.route("/auth/login", methods=["POST"])
def auth_login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    
    print(f"Login attempt: {email}")
    
    if not email or not password:
        flash("Email and password are required.", "error")
        return redirect(url_for("login"))
    
    # Simple validation for testing
    user = db.users.get_user_by_email(email)
    if user and user.get("password") == password:
        session["user_authenticated"] = True
        session["user_email"] = email
        session["user_id"] = user.get("userID")
        flash("Login successful!", "success")
        return redirect(url_for("dashboard"))
    else:
        flash("Invalid email or password.", "error")
        return redirect(url_for("login"))

@app.route("/auth/register", methods=["POST"])
def auth_register():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()
    display_name = request.form.get("display_name", "").strip()
    
    print(f"Register attempt: {email}, {display_name}")
    
    if not email or not password or not display_name:
        flash("All fields are required.", "error")
        return redirect(url_for("register"))
    
    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for("register"))
    
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("register"))
    
    try:
        # Create user
        user_data = db.users.create_user(email, companion="Blayzo")
        db.users.update_user(user_data["userID"], {
            "password": password,
            "display_name": display_name
        })
        
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))
        
    except ValueError as e:
        if "already exists" in str(e):
            flash("Email already registered.", "error")
        else:
            flash("Registration failed.", "error")
        return redirect(url_for("register"))

@app.route("/dashboard")
def dashboard():
    if not session.get("user_authenticated"):
        return redirect(url_for("login"))
    
    user_email = session.get("user_email")
    return f'<h1>Welcome to Dashboard!</h1><p>Logged in as: {user_email}</p><p><a href="/logout">Logout</a></p>'

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    print("Starting SoulBridge Auth Test Server...")
    print("Visit: http://localhost:5000")
    print("Login page: http://localhost:5000/login")
    print("Register page: http://localhost:5000/register")
    
    app.run(debug=True, port=5000)