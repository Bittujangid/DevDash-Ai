import sys
import logging
import pymysql
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the SQLAlchemy object
db = SQLAlchemy()

def run_db_connection_test(app):
    """Performs a direct connection test to the MySQL server on startup.
    Prints host configuration and helpful diagnostic tips on authentication failure.
    """
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    is_sqlite = db_uri.startswith("sqlite")

    print("\n" + "="*60)
    print(" DEVASH AI - DATABASE CONNECTION DIAGNOSTICS")
    print("="*60)
    print(f"Database Host : {Config.DB_HOST}")
    print(f"Database Port : {Config.DB_PORT}")
    print(f"Database Name : {Config.DB_NAME}")
    print(f"Database User : {Config.DB_USER}")
    
    # 1. Handle SQLite bypass for local testing
    if is_sqlite:
        print("Database Type : SQLite (In-Memory Testing Database)")
        print("Connection Status : Connected Successfully (Bypassed MySQL for Testing)")
        print("="*60 + "\n")
        return True

    print("Database Type : MySQL Server")
    
    try:
        # Establish raw connection to MySQL server
        connection = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=int(Config.DB_PORT),
            charset='utf8mb4'
        )
        connection.close()
        print("Connection Status : Connected Successfully")
        print("="*60 + "\n")
        return True
        
    except pymysql.MySQLError as e:
        print("Connection Status : Connection Failed")
        print("="*60)
        
        err_code = e.args[0] if e.args else None
        err_msg = e.args[1] if len(e.args) > 1 else str(e)
        
        print(f"\n[CRITICAL ERROR] Failed to connect to MySQL: {err_msg} (Error Code: {err_code})")
        
        if err_code == 1045:
            # Authentication error (wrong password or username)
            print("\n" + "!"*60)
            print(" MYSQL AUTHENTICATION FAILED (ACCESS DENIED)")
            print("!"*60)
            print("The username or password in your configuration is incorrect.")
            print("\nTo update your database password:")
            print("1. Open the file in your workspace: .env")
            print("2. Find the configuration line: DB_PASSWORD=...")
            print("3. Enter your correct MySQL root password. For example:")
            print("   DB_PASSWORD=krishna@#11219")
            print("4. Save the file and restart the Flask server.")
            print("!"*60 + "\n")
        elif err_code == 2003:
            # Connection refused (MySQL server is not running)
            print("\n" + "!"*60)
            print(" MYSQL SERVER UNREACHABLE")
            print("!"*60)
            print("The MySQL service might not be running or the Host/Port settings are wrong.")
            print("\nPlease ensure:")
            print("1. Your local MySQL Server service is started (e.g. MySQL80).")
            print("2. The DB_HOST and DB_PORT settings in your .env are correct.")
            print("!"*60 + "\n")
            
        return False


def create_database_if_not_exists():
    """Connects to MySQL server raw to ensure the database schema exists."""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=int(Config.DB_PORT),
            charset='utf8mb4'
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                connection.commit()
        finally:
            connection.close()
    except pymysql.MySQLError as e:
        logger.error(f"Failed to verify/create database schema raw: {e}")


def init_db(app):
    """Initializes the database connection, performs diagnostic checks,
    creates schemas, and runs critical production rules.
    """
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    is_sqlite = db_uri.startswith("sqlite")
    
    # Requirement 6: Verify application is using MySQL and not SQLite in production mode
    flask_env = app.config.get("FLASK_ENV", "development").lower()
    if flask_env == "production" and is_sqlite:
        print("\n[CRITICAL SYSTEM SHUTDOWN] production mode violation!")
        print("SQLite databases are STRICTLY PROHIBITED in Production.")
        print("Please configure a valid MySQL DB connection inside your .env variables.")
        sys.exit("Production startup aborted due to SQLite configuration violation.")

    # 1. Run database connection diagnostics
    success = run_db_connection_test(app)
    if not success:
        logger.error("Database connection diagnostics failed. Application startup halted.")
        sys.exit("Database connection failed. Please resolve the credentials mismatch above.")

    # 2. Automatically create database schema if using MySQL
    if not is_sqlite:
        create_database_if_not_exists()
    
    # 3. Bind SQLAlchemy context
    db.init_app(app)
    
    # 4. Create models tables
    with app.app_context():
        import models  # import models here to register tables
        db.create_all()
        
        # Proactive migration: add new user profile columns to MySQL if they don't exist
        if not is_sqlite:
            try:
                from sqlalchemy import text
                # Check existing columns in users table
                result = db.session.execute(text("SHOW COLUMNS FROM users"))
                columns = [row[0] for row in result.fetchall()]
                
                # Add missing columns safely
                if 'linkedin_link' not in columns:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN linkedin_link VARCHAR(255) NULL"))
                    logger.info("Migrated database: users.linkedin_link column added successfully.")
                if 'portfolio_link' not in columns:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN portfolio_link VARCHAR(255) NULL"))
                    logger.info("Migrated database: users.portfolio_link column added successfully.")
                if 'role' not in columns:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(80) NULL DEFAULT 'Developer Workspace'"))
                    logger.info("Migrated database: users.role column added successfully.")
                    
                # Proactive migration for user_settings table
                result_settings = db.session.execute(text("SHOW COLUMNS FROM user_settings"))
                settings_columns = [row[0] for row in result_settings.fetchall()]
                
                if 'show_welcome_banner' not in settings_columns:
                    db.session.execute(text("ALTER TABLE user_settings ADD COLUMN show_welcome_banner TINYINT(1) NOT NULL DEFAULT 1"))
                    logger.info("Migrated database: user_settings.show_welcome_banner column added successfully.")
                if 'show_quick_actions' not in settings_columns:
                    db.session.execute(text("ALTER TABLE user_settings ADD COLUMN show_quick_actions TINYINT(1) NOT NULL DEFAULT 1"))
                    logger.info("Migrated database: user_settings.show_quick_actions column added successfully.")
                if 'sidebar_animation' not in settings_columns:
                    db.session.execute(text("ALTER TABLE user_settings ADD COLUMN sidebar_animation TINYINT(1) NOT NULL DEFAULT 1"))
                    logger.info("Migrated database: user_settings.sidebar_animation column added successfully.")
                    
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to automatically migrate schema columns: {e}")
                
        logger.info("All ORM database tables verified and loaded successfully.")
