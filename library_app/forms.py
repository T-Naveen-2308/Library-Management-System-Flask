from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    ValidationError,
    RadioField,
)
import re
from library_app.models import User
from flask_login import current_user
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=5, max=32)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=60)]
    )
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class EditProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=5, max=60)])
    email = StringField("Email", validators=[DataRequired()])
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=5, max=32)]
    )
    profile_picture = FileField(
        "Profile Picture", validators=[FileAllowed(["jpg", "png", "jpeg"])]
    )
    delete_profile_picture = RadioField(
        "Delete Existing Profile Picture",
        choices=[("yes", "Yes"), ("no", "No")],
        validators=[DataRequired()],
        default="no",
    )
    password = PasswordField(
        "Enter Your Password To Edit",
        validators=[DataRequired(), Length(min=8, max=60)],
    )
    submit = SubmitField("Edit")

    def validate_name(self, name):
        pattern = r"^[A-Za-z\s,'.]{6,60}$"
        if not re.match(pattern, name.data):
            raise ValidationError("Name can only have only have letters, spaces, apostrophes, commas and period.")

    def validate_username(self, username):
        pattern = r"^[a-z][a-z0-9_]{4,31}$"
        if not re.match(pattern, username.data):
            raise ValidationError(
                "Username can only contain lowercase letters, digits and underscore."
            )
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    "That username is already taken. Please choose different username."
                )

    def validate_email(self, email):
        pattern = r"^([a-z\d\.-]+)@([a-z\d-]+)\.([a-z]{2,8})(\.[a-z]{2,8})?$"
        if not re.match(pattern, email.data):
            raise ValidationError("Invalid email address.")
        if email.data != current_user.email:
            email = User.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError(
                    "That email already exists. Please choose a different email."
                )


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(
        "Old Password", validators=[DataRequired(), Length(min=8, max=60)]
    )
    new_password = PasswordField(
        "New Password", validators=[DataRequired(), Length(min=8, max=60)]
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("new_password")]
    )
    submit = SubmitField("Change")

    def validate_new_password(self, new_password):
        pattern = (
            r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()\-_=+{};:,<.>]).{8,60}$"
        )
        if not re.match(pattern, new_password.data):
            raise ValidationError(
                "Password must contain at least eight characters, one uppercase letter, one lowercase letter, one number and one special character."
            )


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField(
        "New Password", validators=[DataRequired(), Length(min=8, max=60)]
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("new_password")]
    )
    submit = SubmitField("Reset Password")

    def validate_new_password(self, new_password):
        pattern = (
            r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()\-_=+{};:,<.>]).{8,60}$"
        )
        if not re.match(pattern, new_password.data):
            raise ValidationError(
                "Password must contain at least eight characters, one uppercase letter, one lowercase letter, one number and one special character."
            )

class DeleteAccountForm(FlaskForm):
    password = PasswordField("Enter Your Password to Confirm", validators=[DataRequired()])
    submit = SubmitField("Delete")
