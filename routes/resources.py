import re
from flask import Blueprint, request, jsonify, session
from database import db
from models import Resource

resources_bp = Blueprint('resources', __name__)

# Basic URL validation regex
URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
    r'localhost|' # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)

@resources_bp.route('/api/resources', methods=['GET'])
def get_resources():
    """Retrieve all saved learning resources for the logged-in user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    resources = Resource.query.filter_by(user_id=user_id).order_by(Resource.created_at.desc()).all()
    return jsonify({
        "success": True,
        "resources": [res.to_dict() for res in resources]
    }), 200


@resources_bp.route('/api/resources', methods=['POST'])
def add_resource():
    """Add a new learning resource for the logged-in user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    url = data.get('url', '').strip()
    category = data.get('category', 'Other').strip().capitalize()  # e.g., 'Documentation', 'Article', 'Course', 'YouTube', 'Other'
    description = data.get('description', '').strip()
    
    # 1. Required fields validation
    if not title or not url:
        return jsonify({"success": False, "message": "Resource title and URL are required."}), 400
        
    # 2. URL format validation
    # If URL doesn't start with http/https, auto-prefix http://
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    if not URL_REGEX.match(url):
        return jsonify({"success": False, "message": "Please enter a valid URL."}), 400
        
    # 3. Category validation
    valid_categories = ['Documentation', 'Article', 'Course', 'YouTube', 'Other']
    if category not in valid_categories:
        # Check case insensitively
        matched = False
        for cat in valid_categories:
            if cat.lower() == category.lower():
                category = cat
                matched = True
                break
        if not matched:
            category = 'Other'
            
    try:
        new_resource = Resource(
            user_id=user_id,
            title=title,
            url=url,
            category=category,
            description=description
        )
        
        db.session.add(new_resource)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Resource saved successfully!",
            "resource": new_resource.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to save resource: {str(e)}"}), 500


@resources_bp.route('/api/resources/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    """Delete a specific saved learning resource."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    resource = Resource.query.filter_by(id=resource_id, user_id=user_id).first()
    if not resource:
        return jsonify({"success": False, "message": "Resource not found or unauthorized access."}), 404
        
    try:
        db.session.delete(resource)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Resource deleted successfully."
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to delete resource: {str(e)}"}), 500
