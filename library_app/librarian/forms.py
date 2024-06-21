from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    SubmitField,
    ValidationError,
    SelectField,
    RadioField,
)
import re
from library_app.models import Section, Book
from wtforms.validators import DataRequired, Length


class AddSectionForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=5, max=60)])
    picture = FileField("Image", validators=[FileAllowed(["jpg", "png", "jpeg"])])
    description = TextAreaField(
        "Description", validators=[DataRequired(), Length(min=10, max=120)]
    )
    submit = SubmitField("Add")

    def validate_title(self, title):
        pattern = r"^[A-Za-z0-9\s\-',.!?]{5,60}$"
        if not re.match(pattern, title.data):
            raise ValidationError(
                "Title can only contain letters, digits, spaces, spaces, hyphens, commas, periods, exclamation and question marks."
            )
        section = Section.query.filter_by(title=title.data).first()
        if section:
            raise ValidationError(
                "That title already exists. Please choose a different title."
            )

    def validate_description(self, description):
        pattern = r"^[\w\s.,!?'\-:;\"()]{10,120}$"
        if not re.match(pattern, description.data):
            raise ValidationError(
                "Description can only contain letters, digits, spaces and punctuation marks."
            )


class EditSectionForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=5, max=60)])
    delete_picture = RadioField(
        "Delete Existing Picture",
        choices=[("yes", "Yes"), ("no", "No")],
        validators=[DataRequired()],
        default="no",
    )
    picture = FileField("Image", validators=[FileAllowed(["jpg", "png", "jpeg"])])
    description = TextAreaField(
        "Description", validators=[DataRequired(), Length(min=10, max=120)]
    )
    submit = SubmitField("Save")

    def __init__(self, current_section, *args, **kwargs):
        super(EditSectionForm, self).__init__(*args, **kwargs)
        self.current_section = current_section

    def validate_title(self, title):
        pattern = r"^[A-Za-z0-9\s\-',.!?]{5,60}$"
        if not re.match(pattern, title.data):
            raise ValidationError(
                "Title can only contain letters, digits, spaces, spaces, hyphens, commas, periods, exclamation and question marks."
            )
        if title.data != self.current_section.title:
            section = Section.query.filter_by(title=title.data).first()
            if section:
                raise ValidationError(
                    "That Section Title already exists. Please choose a different title."
                )

    def validate_description(self, description):
        pattern = r"^[\w\s.,!?'\-:;\"()]{10,120}$"
        if not re.match(pattern, description.data):
            raise ValidationError(
                "Description can only contain letters, digits, spaces and punctuation marks."
            )


class AddBookForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=5, max=60)])
    author = StringField("Author", validators=[DataRequired(), Length(min=5, max=60)])
    picture = FileField("Image", validators=[FileAllowed(["jpg", "png", "jpeg"])])
    pdf_file = FileField("Book PDF", validators=[FileAllowed(["pdf"])])
    sectionid = SelectField("Section", coerce=int)
    description = TextAreaField(
        "Description", validators=[DataRequired(), Length(min=10, max=120)]
    )
    submit = SubmitField("Add")

    def __init__(self, *args, **kwargs):
        super(AddBookForm, self).__init__(*args, **kwargs)
        self.sectionid.choices = [
            (
                section.sectionid,
                section.title if section.title != "Miscellaneous" else "None",
            )
            for section in Section.query.all()
        ]

    def validate_title(self, title):
        pattern = r"^[A-Za-z0-9\s\-',.!?]{5,60}$"
        if not re.match(pattern, title.data):
            raise ValidationError(
                "Title can only contain letters, digits, spaces, spaces, hyphens, commas, periods, exclamation and question marks."
            )
        book = Book.query.filter_by(title=title.data).first()
        if book:
            raise ValidationError(
                "That book title already exists. Please choose a different title."
            )

    def validate_author(self, author):
        pattern = r"^[A-Za-z\s,'.]{5,60}$"
        if not re.match(pattern, author.data):
            raise ValidationError(
                "Author Name can only have only have letters, spaces, apostrophes, commas and period."
            )

    def validate_description(self, description):
        pattern = r"^[\w\s.,!?'\-:;\"()]{10,120}$"
        if not re.match(pattern, description.data):
            raise ValidationError(
                "Description can only contain letters, digits, spaces and punctuation marks."
            )


class EditBookForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=5, max=60)])
    author = StringField("Author", validators=[DataRequired(), Length(min=5, max=60)])
    delete_picture = RadioField(
        "Delete Existing Picture",
        choices=[("yes", "Yes"), ("no", "No")],
        validators=[DataRequired()],
        default="no",
    )
    picture = FileField("Image", validators=[FileAllowed(["jpg", "png", "jpeg"])])
    delete_pdf_file = RadioField(
        "Delete Existing PDF",
        choices=[("yes", "Yes"), ("no", "No")],
        validators=[DataRequired()],
        default="no",
    )
    pdf_file = FileField("Book PDF", validators=[FileAllowed(["pdf"])])
    sectionid = SelectField("Section", coerce=int)
    description = TextAreaField(
        "Description", validators=[DataRequired(), Length(min=10, max=120)]
    )
    submit = SubmitField("Edit")

    def __init__(self, current_book, *args, **kwargs):
        super(EditBookForm, self).__init__(*args, **kwargs)
        self.current_book = current_book
        self.sectionid.choices = [
            (
                section.sectionid,
                section.title if section.title != "Miscellaneous" else "None",
            )
            for section in Section.query.all()
        ]

    def validate_title(self, title):
        pattern = r"^[A-Za-z0-9\s\-',.!?]{5,60}$"
        if not re.match(pattern, title.data):
            raise ValidationError(
                "Title can only contain letters, digits, spaces, spaces, hyphens, commas, periods, exclamation and question marks."
            )
        if title.data != self.current_book.title:
            book = Book.query.filter_by(title=title.data).first()
            if book:
                raise ValidationError(
                    "That Book Title already exists. Please choose a different title."
                )

    def validate_author(self, author):
        pattern = r"^[A-Za-z\s,'.]{5,60}$"
        if not re.match(pattern, author.data):
            raise ValidationError(
                "Author Name can only have only have letters, spaces, apostrophes, commas and period."
            )

    def validate_description(self, description):
        pattern = r"^[\w\s.,!?'\-:;\"()]{10,120}$"
        if not re.match(pattern, description.data):
            raise ValidationError(
                "Description can only contain letters, digits, spaces and punctuation marks."
            )
