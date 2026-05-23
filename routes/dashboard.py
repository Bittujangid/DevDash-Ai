from flask import Blueprint, jsonify, session
from models import Goal, Resource

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Retrieve statistics summary for the developer productivity dashboard."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    try:
        # Query count for goals
        total_goals = Goal.query.filter_by(user_id=user_id).count()
        completed_goals = Goal.query.filter_by(user_id=user_id, completed=True).count()
        pending_goals = total_goals - completed_goals
        
        # Query count for saved resources
        saved_resources = Resource.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_goals": total_goals,
                "completed_goals": completed_goals,
                "pending_goals": pending_goals,
                "saved_resources": saved_resources
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to retrieve stats: {str(e)}"}), 500
