import io
import csv
from flask import Blueprint, request, jsonify, session, Response
from database import db
from models import User, UserSettings

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/api/profile', methods=['GET'])
def get_profile():
    """Retrieve the logged-in user's profile details."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404
        
    return jsonify({
        "success": True,
        "profile": user.to_dict()
    }), 200


@profile_bp.route('/api/profile', methods=['PUT'])
def update_profile():
    """Update the logged-in user's profile details."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404
        
    data = request.get_json() or {}
    
    # Extract profile fields
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    github_username = data.get('github_username', '').strip()
    github_link = data.get('github_link', '').strip()
    bio = data.get('bio', '').strip()
    linkedin_link = data.get('linkedin_link', '').strip()
    portfolio_link = data.get('portfolio_link', '').strip()
    role = data.get('role', '').strip()
    
    # 1. Validation: Username and Email must not be empty if provided
    if 'username' in data and not username:
        return jsonify({"success": False, "message": "Username cannot be empty."}), 400
    if 'email' in data and not email:
        return jsonify({"success": False, "message": "Email cannot be empty."}), 400
        
    # 2. Check for unique username (if changed)
    if username and username != user.username:
        existing = User.query.filter_by(username=username).first()
        if existing:
            return jsonify({"success": False, "message": "Username is already taken by another user."}), 409
        user.username = username
        
    # 3. Check for unique email (if changed)
    if email and email != user.email:
        import re
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            return jsonify({"success": False, "message": "Invalid email address format."}), 400
            
        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({"success": False, "message": "Email is already registered by another user."}), 409
        user.email = email
        
    # Update other fields (always allow updating profile info)
    if 'github_username' in data:
        user.github_username = github_username
        
        # If GitHub username is supplied but no profile link, auto-generate standard GitHub link
        if github_username and not github_link:
            user.github_link = f"https://github.com/{github_username}"
            
    if 'github_link' in data:
        # If a custom link is provided, use it, otherwise keep the generated one
        if github_link:
            user.github_link = github_link
        elif not github_username:
            user.github_link = ""
            
    if 'bio' in data:
        user.bio = bio

    if 'linkedin_link' in data:
        user.linkedin_link = linkedin_link

    if 'portfolio_link' in data:
        user.portfolio_link = portfolio_link

    if 'role' in data:
        user.role = role or "Developer Workspace"
        
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Profile updated successfully!",
            "profile": user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to update profile: {str(e)}"}), 500


@profile_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """Retrieve the logged-in user's settings. Lazily creates it if missing."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404
        
    settings = UserSettings.query.filter_by(user_id=user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Failed to initialize default settings: {str(e)}"}), 500
            
    return jsonify({
        "success": True,
        "settings": settings.to_dict()
    }), 200


@profile_bp.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update the logged-in user's settings."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404
        
    settings = UserSettings.query.filter_by(user_id=user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        
    data = request.get_json() or {}
    
    # Update settings fields
    if 'theme' in data:
        settings.theme = data['theme']
    if 'show_welcome_banner' in data:
        settings.show_welcome_banner = bool(data['show_welcome_banner'])
    if 'show_quick_actions' in data:
        settings.show_quick_actions = bool(data['show_quick_actions'])
    if 'sidebar_animation' in data:
        settings.sidebar_animation = bool(data['sidebar_animation'])
        
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Settings updated successfully!",
            "settings": settings.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to update settings: {str(e)}"}), 500


@profile_bp.route('/api/settings/change-password', methods=['POST'])
def change_password():
    """API endpoint to change user's password securely."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404
        
    data = request.get_json() or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    if not current_password or not new_password or not confirm_password:
        return jsonify({"success": False, "message": "All password fields are required."}), 400
        
    if new_password != confirm_password:
        return jsonify({"success": False, "message": "New passwords do not match."}), 400
        
    if len(new_password) < 8:
        return jsonify({"success": False, "message": "New password must be at least 8 characters long."}), 400
        
    if not user.check_password(current_password):
        return jsonify({"success": False, "message": "Incorrect current password."}), 400
        
    try:
        user.set_password(new_password)
        db.session.commit()
        return jsonify({"success": True, "message": "Password changed successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to update password: {str(e)}"}), 500


@profile_bp.route('/api/settings/export/goals', methods=['GET'])
def export_goals():
    """Export user's goals as a CSV file."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized."}), 401
        
    from models import Goal
    goals = Goal.query.filter_by(user_id=user_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write CSV headers
    writer.writerow(['ID', 'Goal Title', 'Priority', 'Completed', 'Created At'])
    
    for goal in goals:
        writer.writerow([goal.id, goal.title, goal.priority, goal.completed, goal.created_at])
        
    csv_data = output.getvalue()
    output.close()
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=devdash_goals_export.csv"}
    )


@profile_bp.route('/api/settings/export/resources', methods=['GET'])
def export_resources():
    """Export user's learning resources as a CSV file."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized."}), 401
        
    from models import Resource
    resources = Resource.query.filter_by(user_id=user_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write CSV headers
    writer.writerow(['ID', 'Resource Title', 'URL', 'Category', 'Description', 'Created At'])
    
    for res in resources:
        writer.writerow([res.id, res.title, res.url, res.category, res.description, res.created_at])
        
    csv_data = output.getvalue()
    output.close()
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=devdash_resources_export.csv"}
    )


@profile_bp.route('/api/settings/reset-workspace', methods=['POST'])
def reset_workspace():
    """API endpoint to wipe all goals and resources from user's workspace."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized."}), 401
        
    from models import Goal, Resource
    try:
        # Delete all user's goals and resources
        Goal.query.filter_by(user_id=user_id).delete()
        Resource.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({"success": True, "message": "Workspace successfully reset! All goals and resources cleared."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to reset workspace: {str(e)}"}), 500

