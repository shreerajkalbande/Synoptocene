import os
from flask import Flask
from flask_bootstrap import Bootstrap4
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import LoginManager
from dotenv import load_dotenv

from web.models import db, User
from web.routes import main_bp


def create_app(testing: bool = False) -> Flask:
    """Application factory for the Synoptocene Flask app."""
    load_dotenv()

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )

    app.config["SECRET_KEY"] = os.getenv("FLASK_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DB_URI", "sqlite:///posts.db"
    )
    app.config["UPLOAD_FOLDER"] = os.path.join(
        os.path.dirname(__file__), "..", "static", "uploads"
    )

    if testing:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    db.init_app(app)
    CKEditor(app)
    Bootstrap4(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.get_or_404(User, user_id)

    Gravatar(
        app, size=100, rating="g", default="retro",
        force_default=False, force_lower=False, use_ssl=False, base_url=None,
    )

    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
