import unittest
import os
import json
from flask import Flask

# Set testing environment variables before imports
os.environ["SECRET_KEY"] = "testing_secret_key_123"
os.environ["FLASK_ENV"] = "testing"
os.environ["DB_NAME"] = "devdash_ai_test"
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

class DevDashSanityTestCase(unittest.TestCase):
    """Sanity checks for DevDash AI application imports, blueprints, and configuration."""
    
    def test_imports_and_components(self):
        """Test that all core dependencies and custom files import successfully."""
        try:
            from config import Config
            from database import db
            from models import User, Goal, Resource
            print("[OK] Success: All backend classes and SQLAlchemy ORM models imported successfully.")
        except Exception as e:
            self.fail(f"Failure importing app modules: {e}")

    def test_flask_app_instantiation(self):
        """Test that the Flask app can initialize, load configuration, and register blueprints."""
        try:
            from run import app
            # Verify app configurations
            self.assertEqual(app.config["SECRET_KEY"], "testing_secret_key_123")
            
            # Verify registered blueprints
            blueprints = app.blueprints.keys()
            self.assertIn("auth", blueprints)
            self.assertIn("profile", blueprints)
            self.assertIn("goals", blueprints)
            self.assertIn("resources", blueprints)
            self.assertIn("dashboard", blueprints)
            self.assertIn("chat", blueprints)
            print("[OK] Success: Flask app instantiated and all 6 blueprints registered correctly.")
            
        except Exception as e:
            self.fail(f"Failure initializing Flask app structure: {e}")

    def test_offline_ai_chat_simulator(self):
        """Test the offline Gemini AI simulator responses to ensure graceful local execution."""
        try:
            from routes.chat import get_offline_fallback_response
            
            # Test binary search prompt
            reply1 = get_offline_fallback_response("Explain Binary Search")
            self.assertIn("Binary Search", reply1)
            self.assertIn("Offline Simulator Active", reply1)
            
            # Test flask routing prompt
            reply2 = get_offline_fallback_response("Tell me about Flask routing")
            self.assertIn("Flask Routing", reply2)
            self.assertIn("Offline Simulator Active", reply2)
            
            print("[OK] Success: Gemini AI Assistant offline simulator responds correctly with premium layout.")
            
        except Exception as e:
            self.fail(f"Failure in offline chat simulator: {e}")

class DevDashSettingsTestCase(unittest.TestCase):
    """Integration and Unit tests for DevDash AI Settings endpoints and models."""

    def setUp(self):
        # We need to import the app and db here so we don't interfere with initialization order
        from run import app
        from database import db
        self.app = app
        self.client = app.test_client()
        self.db = db
        
        # Create database tables and push context
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.db.create_all()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()

    def register_and_login(self, username="testuser", email="test@example.com", password="password123"):
        # Register user
        self.client.post('/api/register', json={
            "username": username,
            "email": email,
            "password": password
        })
        # Login user
        login_res = self.client.post('/api/login', json={
            "username": username,
            "password": password
        })
        return login_res

    def test_settings_lazy_initialization_and_get(self):
        # 1. Access settings unauthorized -> should fail
        res = self.client.get('/api/settings')
        self.assertEqual(res.status_code, 401)

        # 2. Login
        self.register_and_login()

        # 3. Access settings -> should lazily initialize settings table and return 200
        res = self.client.get('/api/settings')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["settings"]["theme"], "dark")
        self.assertTrue(data["settings"]["show_welcome_banner"])
        self.assertTrue(data["settings"]["show_quick_actions"])
        self.assertTrue(data["settings"]["sidebar_animation"])

    def test_settings_update(self):
        self.register_and_login()
        
        # 1. Update settings
        res = self.client.put('/api/settings', json={
            "theme": "light",
            "show_welcome_banner": False,
            "show_quick_actions": False,
            "sidebar_animation": False
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["settings"]["theme"], "light")
        self.assertFalse(data["settings"]["show_welcome_banner"])
        self.assertFalse(data["settings"]["show_quick_actions"])
        self.assertFalse(data["settings"]["sidebar_animation"])

        # 2. Fetch settings again to verify persistence
        res2 = self.client.get('/api/settings')
        data2 = res2.get_json()
        self.assertEqual(data2["settings"]["theme"], "light")

    def test_change_password(self):
        self.register_and_login()

        # 1. Change password with incorrect current password -> 400
        res = self.client.post('/api/settings/change-password', json={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("Incorrect current password", res.get_json()["message"])

        # 2. Change password with mismatched confirmation -> 400
        res2 = self.client.post('/api/settings/change-password', json={
            "current_password": "password123",
            "new_password": "newpassword123",
            "confirm_password": "mismatched"
        })
        self.assertEqual(res2.status_code, 400)
        self.assertIn("New passwords do not match", res2.get_json()["message"])

        # 3. Change password successfully -> 200
        res3 = self.client.post('/api/settings/change-password', json={
            "current_password": "password123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        })
        self.assertEqual(res3.status_code, 200)

        # 4. Try logging in again with new password
        self.client.post('/api/logout')
        res4 = self.client.post('/api/login', json={
            "username": "testuser",
            "password": "newpassword123"
        })
        self.assertEqual(res4.status_code, 200)

    def test_csv_exports_and_workspace_reset(self):
        self.register_and_login()

        # 1. Add a mock goal and a resource
        from models import Goal, Resource
        goal = Goal(user_id=1, title="Write unit tests", priority="High")
        resource = Resource(user_id=1, title="Flask Testing Docs", url="https://flask.palletsprojects.com/testing/")
        self.db.session.add(goal)
        self.db.session.add(resource)
        self.db.session.commit()

        # 2. Verify export goals CSV
        goals_res = self.client.get('/api/settings/export/goals')
        self.assertEqual(goals_res.status_code, 200)
        self.assertEqual(goals_res.mimetype, "text/csv")
        self.assertIn("Write unit tests", goals_res.data.decode('utf-8'))

        # 3. Verify export resources CSV
        res_res = self.client.get('/api/settings/export/resources')
        self.assertEqual(res_res.status_code, 200)
        self.assertEqual(res_res.mimetype, "text/csv")
        self.assertIn("Flask Testing Docs", res_res.data.decode('utf-8'))

        # 4. Verify workspace reset clears database rows for user
        reset_res = self.client.post('/api/settings/reset-workspace')
        self.assertEqual(reset_res.status_code, 200)
        
        # Check that rows are gone from DB
        self.assertEqual(Goal.query.filter_by(user_id=1).count(), 0)
        self.assertEqual(Resource.query.filter_by(user_id=1).count(), 0)

if __name__ == '__main__':
    print("Running DevDash AI Sanity and Settings Test Suites...")
    unittest.main()
