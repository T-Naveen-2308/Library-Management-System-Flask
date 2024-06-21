import secrets
import os
from PIL import Image
from functools import wraps
from flask import redirect, url_for, current_app, abort, flash
from flask_login import current_user
from flask_mail import Message
from library_app import mail, login_manager


def login_required(role="any"):
    def wrapper(fn):
        @wraps(fn)
        def view(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.get_urole() != role and role!=any:
                abort(403)
            return fn(*args, **kwargs)

        return view

    return wrapper


def check_user():
    def wrapper(fn):
        @wraps(fn)
        def check(*args, **kwargs):
            if current_user.is_authenticated:
                if current_user.get_urole() == "user":
                    return redirect(url_for("user.sections"))
                else:
                    return redirect(url_for("librarian.sections"))
            return fn(*args, **kwargs)

        return check

    return wrapper


def save_picture(picture, path, dim=(350, 350)):
    picture_name = secrets.token_hex(16) + os.path.splitext(picture.filename)[1]
    picture_path = os.path.join(current_app.root_path, "static", path, picture_name)
    newpic = Image.open(picture)
    newpic.thumbnail(dim)
    newpic.save(picture_path)
    return picture_name


def delete_file(path, file):
    file_path = os.path.join(
        current_app.root_path,
        "static",
        path,
        file,
    )
    if os.path.exists(file_path):
        os.remove(file_path)

def send_reset_email(user, func):
    token = user.get_reset_token()
    message = Message(
        "Password Reset Request", sender="noreply@demo.com", recipients=[user.email]
    )
    message.body = f"""To reset your password, visit the following link:
{url_for(func, token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
"""
    mail.send(message)
