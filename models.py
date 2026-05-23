from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    """User DB Model for storing authentication details and profile info."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile fields
    github_username = db.Column(db.String(80), nullable=True)
    github_link = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    linkedin_link = db.Column(db.String(255), nullable=True)
    portfolio_link = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(80), nullable=True, default="Developer Workspace")
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships (cascade delete resources, goals, and settings if user is deleted)
    goals = db.relationship('Goal', backref='user', lazy=True, cascade="all, delete-orphan")
    resources = db.relationship('Resource', backref='user', lazy=True, cascade="all, delete-orphan")
    settings = db.relationship('UserSettings', backref='user', uselist=False, lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """Hashes and sets the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies password hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Returns safe user representation for API calls."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "github_username": self.github_username or "",
            "github_link": self.github_link or "",
            "bio": self.bio or "",
            "linkedin_link": self.linkedin_link or "",
            "portfolio_link": self.portfolio_link or "",
            "role": self.role or "Developer Workspace",
            "created_at": self.created_at.isoformat()
        }


class Goal(db.Model):
    """Goal DB Model for managing developer's daily coding goals."""
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='Medium')  # 'Low', 'Medium', 'High'
    completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serializes goal for REST API."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "priority": self.priority,
            "completed": self.completed,
            "created_at": self.created_at.isoformat()
        }


class Resource(db.Model):
    """Resource DB Model for storing saved developer learning materials."""
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Other')  # 'Documentation', 'Article', 'Course', 'YouTube', 'Other'
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serializes learning resource for REST API."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "url": self.url,
            "category": self.category,
            "description": self.description or "",
            "created_at": self.created_at.isoformat()
        }


class UserSettings(db.Model):
    """User settings DB Model for storing custom dashboard preferences."""
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), unique=True, nullable=False)
    
    # Appearance Settings
    theme = db.Column(db.String(20), default='dark', nullable=False)  # 'dark', 'light', 'system'
    
    # Workspace Preferences
    show_welcome_banner = db.Column(db.Boolean, default=True, nullable=False)
    show_quick_actions = db.Column(db.Boolean, default=True, nullable=False)
    sidebar_animation = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        """Serializes user settings for API."""
        return {
            "theme": self.theme,
            "show_welcome_banner": self.show_welcome_banner,
            "show_quick_actions": self.show_quick_actions,
            "sidebar_animation": self.sidebar_animation
        }

