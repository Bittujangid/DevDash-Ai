from flask import Blueprint, request, jsonify, session
from database import db
from models import Goal

goals_bp = Blueprint('goals', __name__)

@goals_bp.route('/api/goals', methods=['GET'])
def get_goals():
    """Retrieve all coding goals for the logged-in user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    goals = Goal.query.filter_by(user_id=user_id).order_by(Goal.created_at.desc()).all()
    return jsonify({
        "success": True,
        "goals": [goal.to_dict() for goal in goals]
    }), 200


@goals_bp.route('/api/goals', methods=['POST'])
def create_goal():
    """Create a new coding goal for the logged-in user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    priority = data.get('priority', 'Medium').strip().capitalize()  # Standardize casing to 'Low', 'Medium', 'High'
    
    if not title:
        return jsonify({"success": False, "message": "Goal title is required."}), 400
        
    if priority not in ['Low', 'Medium', 'High']:
        priority = 'Medium'
        
    try:
        new_goal = Goal(
            user_id=user_id,
            title=title,
            priority=priority,
            completed=False
        )
        
        db.session.add(new_goal)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Goal created successfully!",
            "goal": new_goal.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to create goal: {str(e)}"}), 500


@goals_bp.route('/api/goals/<int:goal_id>', methods=['PUT'])
def update_goal(goal_id):
    """Update a goal's details (title, priority, or completed status)."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return jsonify({"success": False, "message": "Goal not found or unauthorized access."}), 404
        
    data = request.get_json() or {}
    
    # Update fields if supplied
    if 'title' in data:
        title = data.get('title', '').strip()
        if not title:
            return jsonify({"success": False, "message": "Goal title cannot be empty."}), 400
        goal.title = title
        
    if 'priority' in data:
        priority = data.get('priority', '').strip().capitalize()
        if priority in ['Low', 'Medium', 'High']:
            goal.priority = priority
            
    if 'completed' in data:
        goal.completed = bool(data.get('completed'))
        
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Goal updated successfully!",
            "goal": goal.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to update goal: {str(e)}"}), 500


@goals_bp.route('/api/goals/<int:goal_id>', methods=['DELETE'])
def delete_goal(goal_id):
    """Delete a specific coding goal."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return jsonify({"success": False, "message": "Goal not found or unauthorized access."}), 404
        
    try:
        db.session.delete(goal)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Goal deleted successfully."
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to delete goal: {str(e)}"}), 500
