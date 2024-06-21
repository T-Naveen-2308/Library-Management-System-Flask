from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    ValidationError,
    SelectField,
    IntegerField,
    TextAreaField,
    RadioField,
)
import re
from library_app.models import User, Book
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange


class RegistrationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=4, max=60)])
    email = StringField("Email", validators=[DataRequired()])
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=5, max=32)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=60)]
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    profile_picture = FileField(
        "Profile Picture", validators=[FileAllowed(["jpg", "png", "jpeg"])]
    )
    submit = SubmitField("Register")

    def validate_name(self, name):
        pattern = r"^[A-Za-z\s,'.]{6,60}$"
        if not re.match(pattern, name.data):
            raise ValidationError(
                "Name can only have only have letters, spaces, apostrophes, commas and period."
            )

    def validate_email(self, email):
        pattern = r"^([a-z\d\.-]+)@([a-z\d-]+)\.([a-z]{2,8})(\.[a-z]{2,8})?$"
        if not re.match(pattern, email.data):
            raise ValidationError("Invalid email address.")
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError(
                "That email already exists. Please choose a differenceerent email."
            )

    def validate_username(self, username):
        pattern = r"^[a-z][a-z0-9_]{4,31}$"
        if not re.match(pattern, username.data):
            raise ValidationError(
                "Username can only contain lowercase letters, digits and underscore."
            )
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "That username is already taken. Please choose differenceerent username."
            )

    def validate_password(self, password):
        pattern = (
            r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()\-_=+{};:,<.>]).{8,60}$"
        )
        if not re.match(pattern, password.data):
            raise ValidationError(
                "Password must contain at least eight characters, one uppercase letter, one lowercase letter, one number and one special character."
            )


class BookRequestForm(FlaskForm):
    bookid = SelectField("Book", coerce=int)
    days = IntegerField("Days", validators=[NumberRange(min=1, max=7)])

    def __init__(self, *args, **kwargs):
        super(BookRequestForm, self).__init__(*args, **kwargs)
        self.bookid.choices = [(book.bookid, book.title) for book in Book.query.all()]

    def validate_bookid(self, bookid):
        book = Book.query.filter_by(bookid=bookid.data).first()
        if not book:
            raise ValidationError("That book doesn't exist.")


class FeedbackForm(FlaskForm):
    bookid = SelectField("Book", coerce=int)
    rating = RadioField(
        "Rating",
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")],
        validators=[DataRequired()],
    )
    content = TextAreaField(
        "Content", validators=[DataRequired(), Length(min=10, max=120)]
    )

    def __init__(self, issuedbooks, *args, **kwargs):
        super(FeedbackForm, self).__init__(*args, **kwargs)
        self.bookid.choices = [(issuedbook.book.bookid, issuedbook.book.title) for issuedbook in issuedbooks]

    def validate_bookid(self, bookid):
        book = Book.query.get(bookid.data)
        if not book:
            raise ValidationError("That book doesn't exist.")

    def validate_content(self, content):
        pattern = r"^[\w\s.,!?'\-:;\"()]{10,120}$"
        if not re.match(pattern, content.data):
            raise ValidationError(
                "Content can only contain letters, digits, spaces and punctuation marks."
            )


class EditFeedbackForm(FlaskForm):
    rating = RadioField(
        "Rating",
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")],
        validators=[DataRequired()],
    )
    content = TextAreaField(
        "Content", validators=[DataRequired(), Length(min=10, max=120)]
    )

    def validate_content(self, content):
        pattern = r"^[\w\s.,!?'\-:;\"()]{10,120}$"
        if not re.match(pattern, content.data):
            raise ValidationError(
                "Content can only contain letters, digits, spaces and punctuation marks."
            )
