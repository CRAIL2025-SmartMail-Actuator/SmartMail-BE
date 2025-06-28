from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    migrate = Migrate(app, db)

    # Configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    # Initialize extensions with app
    db.init_app(app)

    # Register blueprints
    from app.routes import main
    from app.authentication import user

    app.register_blueprint(main)
    app.register_blueprint(user)

    return app
