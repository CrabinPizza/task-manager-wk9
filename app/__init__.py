"""Application factory for the task manager."""

import os

from flask import Flask

from app.errors import register_error_handlers
from app.extensions import db


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if config:
        app.config.update(config)

    db.init_app(app)

    from app.routes.stats import bp as stats_bp
    from app.routes.tasks import bp as tasks_bp

    app.register_blueprint(tasks_bp)
    app.register_blueprint(stats_bp)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app
