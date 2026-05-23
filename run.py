import os
from flask import Flask, render_template, send_from_directory
from config import Config
from database import init_db

# 1. Initialize the Flask application
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static"
)

# 2. Load configurations
app.config.from_object(Config)

# 3. Register Blueprints for REST APIs
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.goals import goals_bp
from routes.resources import resources_bp
from routes.dashboard import dashboard_bp
from routes.chat import chat_bp

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(resources_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(chat_bp)

# 4. Route to serve the main HTML page
@app.route('/')
def index():
    """Serves the main single-page-app entry template."""
    return render_template('index.html')

# 5. Initialize Database tables
init_db(app)

if __name__ == '__main__':
    # Determine host and port
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    
    app.logger.info(f"Starting DevDash AI server at http://{host}:{port}/")
    app.run(host=host, port=port, debug=Config.DEBUG)
