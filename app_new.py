"""
Multi-Party Document Verification System on Blockchain

A Flask application for managing financial documents with multi-stakeholder approval workflow.
Supports 5 roles: Content Creator, Censor, Publisher, Customer, and Legal Authority.
"""

import os
from pathlib import Path
from flask import Flask, render_template, session
from config import SECRET_KEY, DEBUG, UPLOAD_DIR, ROLES, STATUS_FLOW
from models.database import DatabaseManager
from routes.auth_routes import auth_bp
from routes.document_routes import document_bp
from routes.approval_routes import approval_bp
from routes.transfer_routes import transfer_bp
from routes.verification_routes import verification_bp
from routes.admin_routes import admin_bp
from routes.dashboard_routes import dashboard_bp


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG
    app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max file size
    
    if config:
        app.config.update(config)
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.init_db()
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(approval_bp)
    app.register_blueprint(transfer_bp)
    app.register_blueprint(verification_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    
    # Context processor for global template variables
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates."""
        user_name = session.get("user_name")
        user_role = session.get("user_role")
        role_info = ROLES.get(user_role, {})
        
        current_user = {
            "is_authenticated": bool(user_name and user_role),
            "name": user_name or "Khách",
            "role": user_role or "Guest",
            "role_label": role_info.get("label", user_role or "Khách"),
            "role_icon": role_info.get("icon", "ph-user"),
            "role_color": role_info.get("color", "#94a3b8"),
        }
        
        return {
            "current_user": current_user,
            "ROLES": ROLES,
            "STATUS_FLOW": STATUS_FLOW,
        }
    
    # Error handlers (commented out - templates not created yet)
    # @app.errorhandler(404)
    # def not_found(error):
    #     """Handle 404 errors."""
    #     return render_template("404.html"), 404
    # 
    # @app.errorhandler(500)
    # def internal_error(error):
    #     """Handle 500 errors."""
    #     return render_template("500.html"), 500
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run the application
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
