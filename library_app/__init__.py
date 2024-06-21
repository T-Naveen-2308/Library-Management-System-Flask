from datetime import datetime, timezone
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from library_app.config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()

login_manager.login_view = "user.login"
login_manager.login_message_category = "info"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from library_app.models import User, Section, Book

    with app.app_context():
        db.create_all()

        section = Section.query.filter_by(title="Miscellaneous").first()

        if not section:
            section = Section(
                title="Miscellaneous",
                description="This section consists of books which do not belong to any other section.",
                picture="default_section_picture.jpeg",
                date_created=datetime.min.replace(tzinfo=timezone.utc).date(),
            )
            db.session.add(section)
            db.session.commit()

    from library_app.main.routes import main
    from library_app.user.routes import user
    from library_app.librarian.routes import librarian
    from library_app.errors.handlers import errors

    app.register_blueprint(main)
    app.register_blueprint(user)
    app.register_blueprint(librarian)
    app.register_blueprint(errors)

    return app
