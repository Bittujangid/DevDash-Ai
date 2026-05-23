import re
from flask import Blueprint, request, jsonify, session
from database import db
from models import User

auth_bp = Blueprint('auth', __name__)

# Regular expressions for validation
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

@auth_bp.route('/api/register', methods=['POST'])
def register():
    """API endpoint to register a new user."""
    data = request.get_json() or {}
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # 1. Required field validation
    if not username or not email or not password:
        return jsonify({"success": False, "message": "All fields (username, email, password) are required."}), 400
        
    # 2. Email format validation
    if not EMAIL_REGEX.match(email):
        return jsonify({"success": False, "message": "Please provide a valid email address."}), 400
        
    # 3. Password minimum 8 characters validation
    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters long."}), 400
        
    # 4. Check for unique username
    existing_username = User.query.filter_by(username=username).first()
    if existing_username:
        return jsonify({"success": False, "message": "Username is already taken."}), 409
        
    # 5. Check for unique email
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({"success": False, "message": "Email is already registered."}), 409
        
    try:
        # Create and save user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "User registered successfully! You can now log in."
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database registration failed: {str(e)}"}), 500


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """API endpoint to log in a user and set their session."""
    data = request.get_json() or {}
    
    username_or_email = data.get('username', '').strip()  # Supports logging in with either username or email
    password = data.get('password', '')
    
    if not username_or_email or not password:
        return jsonify({"success": False, "message": "Username/Email and password are required."}), 400
        
    # Check if input is an email or username
    if EMAIL_REGEX.match(username_or_email):
        user = User.query.filter_by(email=username_or_email).first()
    else:
        user = User.query.filter_by(username=username_or_email).first()
        
    # Validate user credentials
    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "Invalid username/email or password."}), 401
        
    # Store user ID in session
    session['user_id'] = user.id
    session.permanent = True  # Keep session logged in according to app configuration
    
    return jsonify({
        "success": True, 
        "message": f"Welcome back, {user.username}!",
        "user": user.to_dict()
    }), 200


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    """API endpoint to log out a user and clear their session."""
    if 'user_id' in session:
        session.pop('user_id', None)
        return jsonify({"success": True, "message": "Logged out successfully."}), 200
        
    return jsonify({"success": False, "message": "No active session to log out."}), 400


@auth_bp.route('/api/auth/status', methods=['GET'])
def auth_status():
    """API endpoint to check if user is currently authenticated."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"authenticated": False}), 200
        
    user = User.query.get(user_id)
    if not user:
        # Session references a non-existent user, clean it up
        session.pop('user_id', None)
        return jsonify({"authenticated": False}), 200
        
    return jsonify({
        "authenticated": True,
        "user": user.to_dict()
    }), 200
