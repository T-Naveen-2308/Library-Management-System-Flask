from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from library_app import db, bcrypt
from library_app.models import User, Section, Book
from library_app.utils import check_user
from library_app.forms import ResetPasswordForm
from library_app.main.forms import ResetRequestForm
from library_app.utils import send_reset_email

main = Blueprint("main", __name__)


@main.route("/")
@main.route("/home")
@main.route("/sections")
@check_user()
def sections():
    sections = Section.query.order_by(Section.date_created.desc()).all()
    sections.sort(key=lambda x: len(x.books), reverse=True)
    return render_template(
        "main/sections.html",
        title="Sections",
        navbaractive=["Sections"],
        sections=sections,
    )


@main.route("/main/search", methods=["GET", "POST"])
@check_user()
def search():
    if request.method == "POST":
        search_term = request.form["search_term"]
        sections = (
            Section.query.filter(Section.title.ilike(f"%{search_term}%"))
            .order_by(Section.date_created.desc())
            .all()
        )
        books = Book.query.filter(Book.title.ilike(f"%{search_term}%")).all()
        authors = Book.query.filter(Book.author.ilike(f"%{search_term}%")).all()
        return render_template(
            "main/search.html",
            title="Search",
            user=current_user,
            sections=sections,
            books=books,
            authors=authors,
        )
    else:
        return redirect(url_for("main.books"))


@main.route("/section-books/<int:sectionid>")
@check_user()
def section_books(sectionid):
    section = Section.query.get(sectionid)
    sorted_books = sorted(
        section.books,
        key=lambda x: (sum(feedback.rating for feedback in x.feedbacks), x.date_created),
        reverse=True,
    )
    return render_template(
        "main/section_books.html",
        title=f"{section.title} Books",
        navbaractive=["Books"],
        section=section,
        sorted_books=sorted_books,
    )


@main.route("/books")
@check_user()
def books():
    sections = Section.query.order_by(Section.date_created.desc()).all()
    sections.sort(key=lambda x: len(x.books), reverse=True)
    sorted_sections = []
    for section in sections:
        sorted_books = sorted(
            section.books,
            key=lambda x: (
                sum(feedback.rating for feedback in x.feedbacks),
                x.date_created,
            ),
            reverse=True,
        )
        sorted_sections.append((section, sorted_books))
    return render_template(
        "main/books.html",
        title="Books",
        navbaractive=["Books"],
        sorted_sections=sorted_sections,
    )


@main.route("/book-info/<int:bookid>")
@check_user()
def book_info(bookid):
    book = Book.query.get(bookid)
    if book is None:
        flash("Book not found", "danger")
        return redirect(url_for("user.books"))
    feedbacks = sorted(
        book.feedbacks, key=lambda x: (x.rating, x.date_created), reverse=True
    )
    pdf_file = url_for("static", filename="book/pdfs/" + book.pdf_file)
    return render_template(
        "main/book_info.html",
        title="Books",
        book=book,
        feedbacks=feedbacks,
        pdf_file=pdf_file,
        navbaractive=["Books"],
        sections=sections,
    )


@main.route("/reset-request", methods=["GET", "POST"])
@check_user()
def reset_request():
    form = ResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user, 'main.reset_password')
        flash(
            "An email has been sent with instructions to reset your password.", "info"
        )
        if user.get_urole() == "user":
            return redirect(url_for("user.login"))
        else:
            return redirect(url_for("librarian.login"))
    return render_template(
        "main/reset_request.html",
        user=current_user,
        navbaractive=["Login"],
        title="Reset Password",
        form=form,
    )


@main.route("/reset-password/<token>", methods=["GET", "POST"])
@check_user()
def reset_password(token):
    user = User.verify_reset_token(token)
    if user is None:
        flash("That is an invalid or expired token.", "warning")
        return redirect(url_for("main.reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = bcrypt.generate_password_hash(form.new_password.data).decode(
            "utf-8"
        )
        db.session.commit()
        flash("Your password has been updated!", "success")
        if user.get_urole() == "user":
            return redirect(url_for("user.login"))
        else:
            return redirect(url_for("librarian.login"))
    return render_template(
        "main/reset_password.html",
        user=current_user,
        navbaractive=["Login"],
        title="Reset Password",
        form=form,
    )
