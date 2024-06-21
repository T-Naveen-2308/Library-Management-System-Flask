import secrets
from datetime import date, datetime, timezone, timedelta
from flask import (
    request,
    render_template,
    redirect,
    url_for,
    flash,
    abort,
    Blueprint,
)
from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_user, current_user, logout_user
from library_app import db, bcrypt
from library_app.models import User, Section, Book, Request, IssuedBook
from library_app.utils import (
    login_required,
    save_picture,
    send_reset_email,
    delete_file,
)
from library_app.librarian.utils import save_pdf, generate_plots
from library_app.forms import (
    LoginForm,
    EditProfileForm,
    ChangePasswordForm,
    ResetPasswordForm,
    DeleteAccountForm,
)
from library_app.librarian.forms import (
    AddSectionForm,
    EditSectionForm,
    AddBookForm,
    EditBookForm,
)


librarian = Blueprint("librarian", __name__)


@librarian.route("/librarian/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        librarian = User.query.filter_by(username=form.username.data).first()
        if librarian and bcrypt.check_password_hash(
            librarian.password, form.password.data
        ):
            if librarian.urole == "librarian":
                flash("You have logged in successfully!", "success")
                login_user(librarian, remember=form.remember.data)
                nextpage = request.args.get("next")
                return (
                    redirect(nextpage)
                    if nextpage
                    else redirect(url_for("librarian.sections"))
                )
            elif librarian.urole == "user":
                flash("Please log in as user.", "info")
                return redirect(url_for("user.login"))
            else:
                return redirect(url_for("main.error"))
        else:
            flash(f"Invalid Username or Password", "danger")
    return render_template(
        "librarian/login.html",
        title="Login",
        form=form,
        navbaractive=["Login"],
        width=True,
    )


@librarian.route("/librarian/add-section", methods=["GET", "POST"])
@login_required(role="librarian")
def add_section():
    form = AddSectionForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture = save_picture(form.picture.data, "section")
        else:
            picture = "default_section_picture.jpeg"
        section = Section(
            title=form.title.data,
            description=form.description.data,
            picture=picture,
        )
        db.session.add(section)
        db.session.commit()
        flash(f"New Section {form.title.data} created!", "success")
        return redirect(url_for("librarian.sections"))
    return render_template(
        "librarian/add_section.html",
        title="Add Section",
        form=form,
        librarian=current_user,
        navbaractive=["Sections"],
    )


@librarian.route("/librarian/edit-section/<int:sectionid>", methods=["GET", "POST"])
@login_required(role="librarian")
def edit_section(sectionid):
    if sectionid==1:
        abort(403) 
    section = Section.query.get(sectionid)
    form = EditSectionForm(current_section=section)
    if form.validate_on_submit():
        if (
            form.picture.data
            or form.delete_picture.data == "yes"
            or section.title != form.title.data
            or section.description != form.description.data
        ):
            flash("Section has been updated!", "success")
        if form.picture.data:
            if section.picture != "default_section_picture.jpeg":
                delete_file("section", section.picture)
            section.picture = save_picture(form.picture.data, "section")
        elif form.delete_picture.data == "yes":
            if section.picture != "default_section_picture.jpeg":
                delete_file("section", section.picture)
            section.picture = "default_section_picture.jpeg"
        section.date_created = datetime.now(timezone.utc).date()
        section.title = form.title.data
        section.description = form.description.data
        db.session.commit()
        return redirect(url_for("librarian.section_books", sectionid=sectionid))
    if request.method == "GET":
        form.title.data = section.title
        form.description.data = section.description
    return render_template(
        "librarian/edit_section.html",
        title="Edit Section",
        form=form,
        section=section,
        librarian=current_user,
        navbaractive=["Sections"],
    )


@librarian.route("/librarian/delete-section/<int:sectionid>")
@login_required(role="librarian")
def delete_section(sectionid):
    if sectionid==1:
        abort(403)
    section = Section.query.get(sectionid)
    if section:
        try:
            if section.picture != "default_section_picture.jpeg":
                delete_file("section", section.picture)
            for book in section.books:
                book.sectionid = 1
            db.session.commit()
            db.session.delete(section)
            db.session.commit()
            flash("Section deleted successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("An unexpected error occurred while deleting the section.", "error")
    else:
        flash("Section not found.", "error")
    return redirect(url_for("librarian.sections"))


@librarian.route("/librarian/search", methods=["GET", "POST"])
@login_required(role="librarian")
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
            "librarian/search.html",
            title="Search",
            librarian=current_user,
            sections=sections,
            books=books,
            authors=authors,
        )
    else:
        return redirect(url_for("librarian.books"))


@librarian.route("/librarian/sections")
@login_required(role="librarian")
def sections():
    sections = Section.query.order_by(Section.date_created.desc()).all()
    sections.sort(key=lambda x: len(x.books), reverse=True)
    sections.append(None)
    return render_template(
        "librarian/sections.html",
        title="Sections",
        librarian=current_user,
        navbaractive=["Sections"],
        sections=sections,
    )


@librarian.route("/librarian/section-books/<int:sectionid>")
@login_required(role="librarian")
def section_books(sectionid):
    section = Section.query.get(sectionid)
    sorted_books = sorted(
        section.books,
        key=lambda x: (
            sum(feedback.rating for feedback in x.feedbacks),
            x.date_created,
        ),
        reverse=True,
    )
    sorted_books.append(None)
    return render_template(
        "librarian/section_books.html",
        title=f"{section.title} Books",
        librarian=current_user,
        navbaractive=["Books"],
        section=section,
        sorted_books=sorted_books,
    )


@librarian.route("/librarian/add-book/<int:sectionid>", methods=["GET", "POST"])
@login_required(role="librarian")
def add_book(sectionid):
    form = AddBookForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture = save_picture(form.picture.data, "book\\pictures")
        else:
            picture = "default_book_picture.png"
        if form.pdf_file.data:
            pdf_file = save_pdf(form.pdf_file.data, "book\\pdfs")
        else:
            pdf_file = "sample_pdf.pdf"
        book = Book(
            title=form.title.data,
            author=form.author.data,
            picture=picture,
            description=form.description.data,
            sectionid=sectionid,
            pdf_file=pdf_file,
        )
        db.session.add(book)
        db.session.commit()
        flash(f"New Book {form.title.data} created!", "success")
        return redirect(url_for("librarian.section_books", sectionid=sectionid))
    if request.method == "GET":
        form.sectionid.data = sectionid
    return render_template(
        "librarian/add_book.html",
        title="Add Book",
        form=form,
        librarian=current_user,
        navbaractive=["Books"],
    )


@librarian.route("/librarian/edit-book/<int:bookid>", methods=["GET", "POST"])
@login_required(role="librarian")
def edit_book(bookid):
    book = Book.query.get(bookid)
    form = EditBookForm(current_book=book)
    if form.validate_on_submit():
        if (
            form.picture.data
            or form.pdf_file.data
            or form.delete_picture.data == "yes"
            or book.title != form.title.data
            or book.author != form.author.data
            or book.description != form.description.data
            or book.sectionid != book.sectionid.data
        ):
            book.date_created = datetime.now(timezone.utc).date()
            db.session.commit()
            flash("Book has been updated!", "success")
        if form.picture.data:
            if book.picture != "default_book_picture.png":
                delete_file("book\\pictures", book.picture)
            book.picture = save_picture(form.picture.data, "book\\pictures")
        elif form.delete_picture.data == "yes":
            if book.picture != "default_book_picture.png":
                delete_file("book\\pictures", book.picture)
            book.picture = "default_book_picture.png"
        if form.pdf_file.data:
            if book.pdf_file != "sample_pdf.pdf":
                delete_file("book\\pdfs", book.pdf_file)
            book.pdf_file = save_pdf(form.pdf_file.data, "book\\pdfs")
        elif form.delete_pdf_file.data == "yes":
            if book.picture != "sample_pdf.pdf":
                delete_file("book\\pdfs", book.pdf_file)
            book.picture = "sample_pdf.pdf"
        book.title = form.title.data
        book.author = form.author.data
        book.description = form.description.data
        book.sectionid = form.sectionid.data
        db.session.commit()
        return redirect(url_for("librarian.section_book", sectionid=book.sectionid))
    if request.method == "GET":
        form.title.data = book.title
        form.author.data = book.author
        form.description.data = book.description
        form.sectionid.data = book.sectionid
    return render_template(
        "librarian/edit_book.html",
        title="Edit Book",
        form=form,
        book=book,
        librarian=current_user,
        navbaractive=["Books"],
    )


@librarian.route("/librarian/delete-book/<int:place>/<int:bookid>")
@login_required(role="librarian")
def delete_book(place, bookid):
    try:
        book = Book.query.get(bookid)
        sectionid = book.sectionid
        if book:
            if book.picture != "default_book_picture.png":
                delete_file("book\\pictures", book.picture)
            if book.pdf_file != "sample_pdf.pdf":
                delete_file("book\\pdfs", book.pdf_file)
            db.session.delete(book)
            db.session.commit()
            flash("The book has been deleted.", "success")
        else:
            flash("Book not found.", "danger")
    except SQLAlchemyError:
        db.session.rollback()
        flash("An unexpected error occurred while deleting the book.", "danger")
    if place:
        return redirect(url_for("librarian.books"))
    else:
        return redirect(url_for("librarian.section_books", sectionid=sectionid))


@librarian.route("/librarian/books")
@login_required(role="librarian")
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
        "librarian/books.html",
        title="Books",
        librarian=current_user,
        navbaractive=["Books"],
        sorted_sections=sorted_sections,
    )


@librarian.route("/librarian/book-info/<int:bookid>")
@login_required(role="librarian")
def book_info(bookid):
    book = Book.query.get(bookid)
    if book is None:
        flash("Book not found", "danger")
        return redirect(url_for("user.books"))
    feedbacks = sorted(
        book.feedbacks, key=lambda x: (x.rating, x.date_created), reverse=True
    )
    pdf_file = url_for("static", filename="book/pdfs/" + book.pdf_file)
    issuedbooks = (
        IssuedBook.query.filter(
            IssuedBook.bookid == bookid, IssuedBook.status == "current"
        )
        .order_by(IssuedBook.to_date.desc())
        .all()
    )
    print(issuedbooks)
    return render_template(
        "librarian/book_info.html",
        title="Books",
        librarian=current_user,
        book=book,
        issuedbooks=issuedbooks,
        feedbacks=feedbacks,
        pdf_file=pdf_file,
        navbaractive=["Books"],
        sections=sections,
    )


@librarian.route("/librarian/view-book/<int:bookid>")
@login_required(role="librarian")
def view_book(bookid):
    book = Book.query.get(bookid)
    pdf_file = url_for("static", filename="book/pdfs/" + book.pdf_file)
    return render_template(
        "librarian/view_book.html",
        title="View Book",
        book=book,
        librarian=current_user,
        pdf_file=pdf_file,
        navbactive=["MyBooks"],
    )


@librarian.route("/librarian/requests")
@login_required(role="librarian")
def requests():
    outdated_requests = Request.query.filter_by(status="pending").all()
    for outdated_request in outdated_requests:
        if ((outdated_request.date_created + timedelta(days=7)) < date.today()):
            outdated_request.status = "rejected"
    db.session.commit()
    requests = (
        Request.query.filter_by(status="pending").order_by(Request.date_created).all()
    )
    issuedbooks = IssuedBook.query.filter_by(status="current").all()
    for issuedbook in issuedbooks:
        if datetime.now(timezone.utc).date() > issuedbook.to_date:
            issuedbook.status = "returned"
    db.session.commit()
    rejectedbooks = (
        Request.query.filter_by(status="rejected")
        .order_by(Request.date_created.desc())
        .all()
    )
    issuedbooks = (
        IssuedBook.query.filter_by(status="current")
        .order_by(IssuedBook.to_date.desc())
        .all()
    )
    return render_template(
        "librarian/requests.html",
        title="Requests",
        requests=requests,
        issuedbooks=issuedbooks,
        librarian=current_user,
        rejectedbooks = rejectedbooks,
        navbaractive=["Requests"],
    )


@librarian.route("/librarian/grant-request/<int:requestid>")
@login_required(role="librarian")
def grant_request(requestid):
    user_request = Request.query.get(requestid)
    if user_request.status!="pending":
        flash(f"The request has already been {user_request.status}.", "danger")
        return redirect(url_for("librarian.requests"))
    user_request.status = "accepted"
    db.session.commit()
    issuedbook = IssuedBook(
        userid=user_request.userid,
        issued_by=current_user.userid,
        bookid=user_request.bookid,
        from_date=datetime.now(timezone.utc).date(),
        to_date=(datetime.now(timezone.utc).date() + timedelta(days=user_request.days)),
    )
    flash("The Request has been granted.", "success")
    db.session.add(issuedbook)
    db.session.commit()
    return redirect(url_for("librarian.requests"))


@librarian.route("/librarian/reject-request/<int:requestid>")
@login_required(role="librarian")
def reject_request(requestid):
    user_request = Request.query.get(requestid)
    if user_request.status!="pending":
        flash(f"The request has already been {user_request.status}.", "danger")
        return redirect(url_for("librarian.requests"))
    user_request.status ="rejected"
    db.session.commit()
    flash("The Request has been rejected.", "danger")
    return redirect(url_for("librarian.requests"))


@librarian.route("/librarian/revoke-access/<int:issueid>")
@login_required(role="librarian")
def revoke_access(issueid):
    issuedbook = IssuedBook.query.get(issueid)
    if issuedbook.status=="returned":
        flash(f"The book has already been returned.", "danger")
        return redirect(url_for("librarian.requests"))
    issuedbook.status = "returned"
    issuedbook.to_date = datetime.now(timezone.utc).date()
    db.session.commit()
    flash("The access has been revoked.", "danger")
    return redirect(url_for("librarian.requests"))


@librarian.route("/librarian/stats")
@login_required(role="librarian")
def stats():
    generate_plots()
    return render_template(
        "librarian/stats.html",
        title="Stats",
        librarian=current_user,
        navbaractive=["Stats"],
    )


previous_user = None


@librarian.route("/librarian/account")
@login_required(role="librarian")
def account():
    global previous_user
    previous_user = None
    return render_template(
        "librarian/account.html",
        title="Account",
        librarian=current_user,
        navbaractive=["Account"],
    )


@librarian.route("/librarian/reset-request/<int:token>", methods=["GET", "POST"])
@login_required(role="librarian")
def reset_request(token):
    send_reset_email(current_user, "librarian.reset_password")
    flash("An email has been sent with instructions to reset your password.", "info")
    if token == 1:
        return redirect(url_for("librarian.edit_profile"))
    elif token == 2:
        return redirect(url_for("librarian.change_password"))
    else:
        return redirect(url_for("librarian.delete_account"))


@librarian.route("/librarian/reset-password/<token>", methods=["GET", "POST"])
@login_required(role="librarian")
def reset_password(token):
    librarian = User.verify_reset_token(token)
    if librarian is None:
        flash("That is an invalid or expired token.", "warning")
        return redirect(url_for("librarian.account"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        librarian.password = bcrypt.generate_password_hash(
            form.new_password.data
        ).decode("utf-8")
        db.session.commit()
        flash("Your password has been updated! Please log in again.", "success")
        logout_user()
        return redirect(url_for("librarian.login"))
    return render_template(
        "librarian/reset_password.html",
        librarian=current_user,
        navbaractive=["Account"],
        title="Reset Password",
        form=form,
    )


@librarian.route("/librarian/edit-profile", methods=["GET", "POST"])
@login_required(role="librarian")
def edit_profile():
    form = EditProfileForm()
    global previous_user
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.password.data):
            previous_user = None
            if (
                form.profile_picture.data
                or form.delete_profile_picture.data == "yes"
                or current_user.name != form.name.data
                or current_user.email != form.email.data
                or current_user.username != form.username.data
            ):
                flash("Your account has been updated!", "success")
            if form.profile_picture.data:
                if current_user.profile_picture != "default_profile_picture.png":
                    delete_file(
                        "librarian\\profile_pictures", current_user.profile_picture
                    )
                current_user.profile_picture = save_picture(
                    form.profile_picture.data, "librarian\\profile_pictures"
                )
            elif form.delete_profile_picture.data == "yes":
                if current_user.profile_picture != "default_profile_picture.png":
                    delete_file(
                        "librarian\\profile_pictures", current_user.profile_picture
                    )
                current_user.profile_picture = "default_profile_picture.png"
            current_user.name = form.name.data
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            return redirect(url_for("librarian.account"))
        else:
            picture = "default_profile_pic.png"
            previous_user = User(
                name=form.name.data,
                email=form.email.data,
                username=form.username.data,
                password=secrets.token_hex(16),
                picture=picture,
            )
            flash("The password is incorrect.", "danger")
            return redirect(url_for("librarian.edit_profile"))
    if request.method == "GET":
        if previous_user:
            form.name.data = previous_user.name
            form.username.data = previous_user.username
            form.email.data = previous_user.email
        else:
            form.name.data = current_user.name
            form.username.data = current_user.username
            form.email.data = current_user.email
    return render_template(
        "librarian/edit_profile.html",
        title="Update Profile",
        librarian=current_user,
        form=form,
        navbaractive=["Account"],
    )


@librarian.route("/librarian/change-password", methods=["GET", "POST"])
@login_required(role="librarian")
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.old_password.data):
            if not bcrypt.check_password_hash(
                current_user.password, form.new_password.data
            ):
                flash("Your password has been updated!", "success")
            current_user.password = bcrypt.generate_password_hash(
                form.new_password.data
            ).decode("utf-8")
            db.session.commit()
            return redirect(url_for("librarian.account"))
        else:
            flash("The password is incorrect.", "danger")
            return redirect(url_for("librarian.change_password"))
    return render_template(
        "librarian/change_password.html",
        title="Change Password",
        librarian=current_user,
        form=form,
        navbaractive=["Account"],
    )


@librarian.route("/librarian/delete-account")
@login_required(role="librarian")
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.password.data):
            if current_user.profile_picture != "default_profile_picture.png":
                delete_file(
                    "librarin\\profile_pictures", current_user.profile_picture
                )
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            return redirect(url_for("main.sections"))
        else:
            flash("The password is incorrect.", "danger")
            return redirect(url_for("librarian.delete_account"))
    return render_template(
        "librarian/delete_account.html",
        title="Delete Account",
        librarian=current_user,
        form=form,
        navbaractive=["Account"],
    )


@librarian.route("/librarian/logout")
@login_required(role="librarian")
def logout():
    logout_user()
    return redirect(url_for("main.sections"))
