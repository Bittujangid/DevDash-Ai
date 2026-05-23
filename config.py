import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class loaded from environment variables."""
    
    # Flask configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_dash_secret_session_key_default_321")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"

    # MySQL connection configuration
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "devdash_ai")

    # Safely URL-encode password to support special characters (@, #, :, etc.) in connection URI
    _encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""

    # SQLAlchemy database URI
    # Supports overriding via env variable (e.g. sqlite:///:memory: for testing)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI") or f"mysql+pymysql://{DB_USER}:{_encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google Gemini API configurations
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
