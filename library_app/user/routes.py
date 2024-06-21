import secrets
from datetime import datetime, timezone
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    abort,
    request,
)
from flask_login import login_user, current_user, logout_user
from library_app import db, bcrypt
from library_app.models import User, Section, Request, Feedback, IssuedBook, Book
from library_app.forms import (
    LoginForm,
    EditProfileForm,
    ChangePasswordForm,
    ResetPasswordForm,
    DeleteAccountForm,
)
from library_app.user.forms import (
    RegistrationForm,
    BookRequestForm,
    FeedbackForm,
    EditFeedbackForm,
)
from library_app.utils import (
    login_required,
    check_user,
    save_picture,
    send_reset_email,
    delete_file,
)
from library_app.user.utils import generate_plots

user = Blueprint("user", __name__)


@user.route("/user/register", methods=["GET", "POST"])
@check_user()
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.profile_picture.data:
            profile_picture = save_picture(form.profile_picture.data, "user\\profile_pictures")
        else:
            profile_picture = "default_profile_picture.png"
        user = User(
            name=form.name.data,
            email=form.email.data,
            username=form.username.data,
            password=form.password.data,
            profile_picture=profile_picture,
        )
        print(form.profile_picture.data, user)
        db.session.add(user)
        db.session.commit()
        flash(f"Account created for {form.username.data}!", "success")
        return redirect(url_for("user.login"))
    return render_template(
        "user/register.html",
        user=current_user,
        title="Register",
        form=form,
        navbaractive=["Login"],
    )


@user.route("/user/login", methods=["GET", "POST"])
@check_user()
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.urole == "user":
                flash(f"You have logged in successfully!", "success")
                login_user(user, remember=form.remember.data)
                nextpage = request.args.get("next")
                return (
                    redirect(nextpage) if nextpage else redirect(url_for("user.books"))
                )
            elif user.urole == "librarian":
                flash(f"Please log in as librarian", "info")
                return redirect(url_for("librarian.login"))
            else:
                return redirect(url_for("main.error"))
        else:
            flash(f"Invalid username or Password", "danger")
    return render_template(
        "user/login.html", title="Login", form=form, navbaractive=["Login"], width=True
    )


@user.route("/user/sections")
@login_required(role="user")
def sections():
    sections = Section.query.order_by(Section.date_created.desc()).all()
    sections.sort(key=lambda x: len(x.books), reverse=True)
    return render_template(
        "user/sections.html",
        title="Sections",
        navbaractive=["Sections"],
        user=current_user,
        sections=sections,
    )


@user.route("/user/search", methods=["GET", "POST"])
@login_required(role="user")
def search():
    if request.method == "POST":
        search_term = request.form["search_term"]
        sections = (
            Section.query.filter(Section.title.ilike(f"%{search_term}%"))
            .order_by(Section.date_created.desc())
            .all()
        )
        books = Book.query.filter(Book.title.ilike(f"%{search_term}%")).all()
        books.sort(
            key=lambda x: (
                sum(feedback.rating for feedback in x.feedbacks),
                x.date_created,
            ),
            reverse=True,
        )
        authors = Book.query.filter(Book.author.ilike(f"%{search_term}%")).all()
        authors.sort(
            key=lambda x: (
                sum(feedback.rating for feedback in x.feedbacks),
                x.date_created,
            ),
            reverse=True,
        )
        return render_template(
            "user/search.html",
            title="Search",
            user=current_user,
            sections=sections,
            books=books,
            authors=authors,
        )
    else:
        return redirect(url_for("user.books"))


@user.route("/user/section-books/<int:sectionid>")
@login_required(role="user")
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
    return render_template(
        "user/section_books.html",
        title=f"{section.title} Books",
        user=current_user,
        navbaractive=["Books"],
        section=section,
        sorted_books=sorted_books,
    )


@user.route("/user/books")
@login_required(role="user")
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
    issuedbookids = {
        issuedbook.bookid: issuedbook.issueid
        for issuedbook in current_user.issuedbooks
        if issuedbook.status == "current"
    }
    feedbackbookids = {
        feedback.bookid: feedback.feedbackid
        for feedback in current_user.feedbacks
        if feedback.bookid in issuedbookids
    }
    return render_template(
        "user/books.html",
        title="Books",
        user=current_user,
        navbaractive=["Books"],
        issuedbookids=issuedbookids,
        feedbackbookids=feedbackbookids,
        sorted_sections=sorted_sections,
    )


@user.route("/user/book-info/<int:bookid>")
@login_required(role="user")
def book_info(bookid):
    book = Book.query.get(bookid)
    if book is None:
        flash("Book not found", "danger")
        return redirect(url_for("user.books"))
    feedbacks = sorted(
        book.feedbacks, key=lambda x: (x.rating, x.date_created), reverse=True
    )
    pdf_file = url_for("static", filename="book/pdfs/" + book.pdf_file)
    issuedbookids = {
        issuedbook.bookid: issuedbook.issueid
        for issuedbook in current_user.issuedbooks
        if issuedbook.status == "current"
    }
    feedbackbookids = {
        feedback.bookid: feedback.feedbackid
        for feedback in current_user.feedbacks
        if feedback.bookid in issuedbookids
    }
    return render_template(
        "user/book_info.html",
        title="Books",
        user=current_user,
        book=book,
        feedbacks=feedbacks,
        issuedbookids=issuedbookids,
        feedbackbookids=feedbackbookids,
        pdf_file=pdf_file,
        navbaractive=["Books"],
        sections=sections,
    )


@user.route("/user/book-request/<int:bookid>", methods=["GET", "POST"])
@login_required(role="user")
def book_request(bookid):
    cou1 = 0
    for issuedbook in current_user.issuedbooks:
        if issuedbook.bookid == bookid and issuedbook.status=="current":
            flash("The book has already been issued.", "info")
            return redirect(url_for("user.books"))
        if issuedbook.status == "current":
            cou1 += 1
    cou2 = 0
    for user_request in current_user.requests:
        if user_request.bookid == bookid and user_request.status == "pending":
            flash("The request has already been placed.", "info")
            return redirect(url_for("user.books"))
        if user_request.status == "pending":
            cou2 += 1
    if cou1 + cou2 >= 5:
        flash("You can only borrow 5 books at maximum.", "danger")
        return redirect(url_for("user.mybooks"))
    form = BookRequestForm()
    if form.validate_on_submit():
        book_request = Request(
            userid=current_user.userid,
            days=form.days.data,
            bookid=form.bookid.data,
        )
        db.session.add(book_request)
        db.session.commit()
        flash(f"The book has been requested!", "success")
        return redirect(url_for("user.mybooks"))
    if request.method == "GET":
        form.bookid.data = bookid
        form.days.data = 3
    return render_template(
        "user/book_request.html",
        title="Book Request",
        form=form,
        user=current_user,
        navbaractive=["Books"],
    )


@user.route("/user/delete-request/<int:requestid>")
@login_required(role="user")
def delete_request(requestid):
    book_request = Request.query.get(requestid)
    if book_request:
        if current_user.userid == book_request.userid:
            flash("The request has been deleted.", "success")
            db.session.delete(book_request)
            db.session.commit()
        else:
            abort(403)
    else:
        flash("The book doesn't exist", "danger")
    return redirect(url_for("user.mybooks"))


@user.route("/user/mybooks")
@login_required(role="user")
def mybooks():
    current, completed = [], []
    for issuedbook in IssuedBook.query.filter_by(userid=current_user.userid).all():
        if issuedbook.status == "current":
            if datetime.now(timezone.utc).date() > issuedbook.to_date:
                issuedbook.status = "returned"
                db.session.commit()
        if issuedbook.status == "current":
            current.append(issuedbook)
        else:
            completed.append(issuedbook)
    current.sort(
        key=lambda x: (
            x.to_date,
            -sum(feedback.rating for feedback in x.book.feedbacks),
        )
    )
    current2 = []
    for issuedbook in current:
        feedbackid = None
        for feedback in issuedbook.book.feedbacks:
            if current_user.userid == feedback.userid:
                feedbackid = feedback.feedbackid
                break
        current2.append((feedbackid, issuedbook))
    completed.sort(
        key=lambda x: (
            x.to_date,
            sum(feedback.rating for feedback in x.book.feedbacks),
        ),
        reverse=True,
    )
    requests = list(current_user.requests)
    status_order = {"pending": 0, "rejected": 1, "accepted": 2}
    requests.sort(key=lambda x: (status_order[x.status], x.date_created))
    return render_template(
        "user/mybooks.html",
        title="MyBooks",
        user=current_user,
        current2=current2,
        completed=completed,
        requests=requests,
        status_order=status_order,
        navbaractive=["MyBooks"],
    )


@user.route("/user/view-book/<int:bookid>")
@login_required(role="user")
def view_book(bookid):
    for issuedbook in current_user.issuedbooks:
        if datetime.now(timezone.utc).date() > issuedbook.to_date:
            issuedbook.status = "returned"
    db.session.commit()
    flag = True
    for issuedbook in current_user.issuedbooks:
        if issuedbook.status == "current" and issuedbook.bookid == bookid:
            flag = False
            break
    if flag:
        abort(403)
    book = Book.query.get(bookid)
    pdf_file = url_for("static", filename="book/pdfs/" + book.pdf_file)
    return render_template(
        "user/view_book.html",
        title="View Book",
        book=book,
        user=current_user,
        pdf_file=pdf_file,
        navbactive=["MyBooks"],
    )


@user.route("/user/return-book/<int:issueid>")
@login_required(role="user")
def return_book(issueid):
    issuedbook = IssuedBook.query.get(issueid)
    if issuedbook.userid != current_user.userid:
        abort(403)
    if issuedbook.status == "returned":
        return redirect(url_for("user.mybooks"))
    issuedbook.status = "returned"
    issuedbook.to_date = datetime.now(timezone.utc).date()
    db.session.commit()
    flash("The Book has been returned successfully.", "success")
    return redirect(url_for("user.mybooks"))


@user.route("/user/book-feedback/<int:bookid>", methods=["GET", "POST"])
@login_required(role="user")
def book_feedback(bookid):
    book = Book.query.get(bookid)
    if book is None:
        flash("Book not found", "danger")
        return redirect(url_for("user.mybooks"))
    if not (
        any(issuedbook.bookid == bookid for issuedbook in current_user.issuedbooks)
    ):
        flash(f"You can only give feedback of the books you borrowed.", "info")
        return redirect(url_for("user.mybooks"))
    if any(feedback.userid == current_user.userid for feedback in book.feedbacks):
        flash(
            "You can only give one feedback. Please edit your existing feedback.",
            "info",
        )
        return redirect(url_for("user.mybooks"))
    form = FeedbackForm(current_user.issuedbooks)
    if form.validate_on_submit():
        try:
            if not (
                any(
                    issuedbook.bookid == form.bookid.data
                    for issuedbook in current_user.issuedbooks
                )
            ):
                flash(f"You can only give feedback of the books you borrowed.", "info")
                return redirect(url_for("user.mybooks"))
            if any(
                feedback.userid == current_user.userid
                and feedback.bookid == form.bookid.data
                for feedback in Feedback.query.all()
            ):
                flash(
                    "You can only give one feedback. Please edit your existing feedback.",
                    "info",
                )
                return redirect(url_for("user.mybooks"))
            feedback = Feedback(
                userid=current_user.userid,
                bookid=form.bookid.data,
                rating=form.rating.data,
                content=form.content.data,
            )
            db.session.add(feedback)
            db.session.commit()
            flash("Thanks for giving your feedback!", "success")
        except Exception as e:
            db.session.rollback()
            print(e)
            flash("An error occurred while giving feedback.", "danger")
        return redirect(url_for("user.mybooks"))
    if request.method == "GET":
        form.rating.default = 5
        form.process()
        form.bookid.data = bookid
    return render_template(
        "user/book_feedback.html",
        title="Feedback",
        form=form,
        user=current_user,
        navbaractive=["MyBooks"],
    )


@user.route("/user/edit-feedback/<int:feedbackid>", methods=["GET", "POST"])
@login_required(role="user")
def edit_feedback(feedbackid):
    feedback = Feedback.query.get(feedbackid)
    if current_user.userid != feedback.userid:
        abort(403)
    if not (
        any(
            issuedbook.bookid == feedback.bookid
            for issuedbook in current_user.issuedbooks
        )
    ):
        flash(f"You can only give feedback of the books you borrowed.", "info")
        return redirect(url_for("user.mybooks"))
    form = EditFeedbackForm()
    if form.validate_on_submit():
        try:
            if (
                feedback.rating != form.rating.data
                or feedback.content != form.content.data
            ):
                flash("Your feedback has been edited!", "success")
            feedback.rating = form.rating.data
            feedback.content = form.content.data
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("An error occurred while removing the completed book.", "danger")
        return redirect(url_for("user.mybooks"))
    if request.method == "GET":
        form.rating.default = feedback.rating
        form.process()
        form.content.data = feedback.content
    return render_template(
        "user/edit_feedback.html",
        title="Feedback",
        form=form,
        user=current_user,
        navbaractive=["MyBooks"],
    )


@user.route("/user/stats")
@login_required(role="user")
def stats():
    generate_plots()
    return render_template(
        "user/stats.html", title="Stats", user=current_user, navbaractive=["Stats"]
    )


previous_user = None


@user.route("/user/account")
@login_required(role="user")
def account():
    global previous_user
    previous_user = None
    return render_template(
        "user/account.html",
        title="Account",
        user=current_user,
        navbaractive=["Account"],
    )


@user.route("/user/reset-request/<int:token>", methods=["GET", "POST"])
@login_required(role="user")
def reset_request(token):
    send_reset_email(current_user, "user.reset_password")
    flash("An email has been sent with instructions to reset your password.", "info")
    if token == 1:
        return redirect(url_for("user.edit_profile"))
    else:
        return redirect(url_for("user.change_password"))


@user.route("/user/reset-password/<token>", methods=["GET", "POST"])
@login_required(role="user")
def reset_password(token):
    user = User.verify_reset_token(token)
    if user is None:
        flash("That is an invalid or expired token.", "warning")
        return redirect(url_for("user.account"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = bcrypt.generate_password_hash(form.new_password.data).decode(
            "utf-8"
        )
        db.session.commit()
        flash("Your password has been updated! Please log in again.", "success")
        logout_user()
        return redirect(url_for("user.login"))
    return render_template(
        "user/reset_password.html",
        user=current_user,
        navbaractive=["Account"],
        title="Reset Password",
        form=form,
    )


@user.route("/user/edit-profile", methods=["GET", "POST"])
@login_required(role="user")
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
                    delete_file("user\\profile_pictures", current_user.profile_picture)
                current_user.profile_picture = save_picture(
                    form.profile_picture.data, "user\\profile_pictures"
                )
            elif form.delete_profile_picture.data:
                if current_user.profile_picture != "default_profile_picture.png":
                    delete_file("user\\profile_pictures", current_user.profile_picture)
                current_user.profile_picture = "default_profile_picture.png"
            current_user.name = form.name.data
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            return redirect(url_for("user.account"))
        else:
            profile_picture = "default_profile_pic.png"
            previous_user = User(
                name=form.name.data,
                email=form.email.data,
                username=form.username.data,
                password=secrets.token_hex(16),
                profile_picture=profile_picture,
            )
            flash("The password is incorrect.", "danger")
            return redirect(url_for("user.edit_profile"))
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
        "user/edit_profile.html",
        title="Update Profile",
        user=current_user,
        form=form,
        navbaractive=["Account"],
    )


@user.route("/user/change-password", methods=["GET", "POST"])
@login_required(role="user")
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
            return redirect(url_for("user.account"))
        else:
            flash("The password is incorrect.", "danger")
            return redirect(url_for("user.change_password"))
    return render_template(
        "user/change_password.html",
        title="Change Password",
        user=current_user,
        form=form,
        navbaractive=["Account"],
    )


@user.route("/user/delete-account", methods=["GET", "POST"])
@login_required(role="user")
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.password.data):
            if current_user.profile_picture != "default_profile_picture.png":
                delete_file("user\\profile_pictures", current_user.profile_picture)
            delete_file("user\\stats", f"{current_user.username}_bar_chart.png")
            delete_file("user\\stats", f"{current_user.username}_pie_chart.png")
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            return redirect(url_for("main.sections"))
        else:
            flash("The password is incorrect.", "danger")
            return redirect(url_for("user.delete_account"))
    return render_template(
        "user/delete_account.html",
        title="Delete Account",
        user=current_user,
        form=form,
        navbaractive=["Account"],
    )


@user.route("/user/logout")
@login_required(role="user")
def logout():
    logout_user()
    return redirect(url_for("main.sections"))
