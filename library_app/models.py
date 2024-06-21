import jwt
from datetime import datetime, timedelta, timezone
from flask import current_app
from library_app import db, login_manager, bcrypt
from sqlalchemy import CheckConstraint


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)


class User(db.Model):
    __tablename__ = "user"
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(60), nullable=False)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    profile_picture = db.Column(
        db.String(20), nullable=False, default="default_profile_picture.png"
    )
    authenticated = db.Column(db.Boolean, default=False)
    urole = db.Column(db.String(20), default="user")
    requests = db.relationship(
        "Request", back_populates="user", lazy=True, cascade="all, delete-orphan"
    )
    feedbacks = db.relationship(
        "Feedback", back_populates="user", lazy=True, cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(urole.in_(["user", "librarian"]), name="check_urole"),
    )

    def __repr__(self):
        return f"User('{self.userid}', '{self.name}', '{self.username}', '{self.email}', '{self.password}', '{self.profile_picture}', '{self.authenticated}', '{self.urole}')"

    def __init__(
        self,
        name,
        username,
        email,
        password,
        profile_picture,
        authenticated=False,
        urole="user",
    ):
        self.name = name
        self.email = email
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        self.profile_picture = profile_picture
        self.authenticated = authenticated
        self.urole = urole

    def get_reset_token(self, expires_sec=1800):
        secret_key = jwt.encode(
            {
                "userid": self.userid,
                "exp": datetime.now(timezone.utc)
                + timedelta(seconds=expires_sec),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        return secret_key

    @staticmethod
    def verify_reset_token(token):
        try:
            data = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                leeway=timedelta(seconds=10),
                algorithms=["HS256"],
                options={"verify_exp": True},
            )
        except:
            return None
        return User.query.filter(User.userid == int(data["userid"])).first()

    def is_active(self):
        return True

    def get_id(self):
        return self.userid

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def get_urole(self):
        return self.urole


class Section(db.Model):
    __tablename__ = "section"
    sectionid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(60), unique=True, nullable=False)
    date_created = db.Column(
        db.Date, nullable=False, default=datetime.now(timezone.utc).date()
    )
    picture = db.Column(
        db.String(20), nullable=False, default="default_section_picture.jpeg"
    )
    description = db.Column(db.String(120), nullable=False)
    books = db.relationship("Book", back_populates="section", lazy=True)

    def __init__(
        self,
        title,
        description,
        picture,
        date_created=datetime.now(timezone.utc),
    ):
        self.title = title
        self.description = description
        self.picture = picture
        self.date_created = date_created

    def __repr__(self):
        return f"Section('{self.sectionid}', '{self.title}', '{self.date_created}', '{self.description}', '{self.picture}')"


class Book(db.Model):
    __tablename__ = "book"
    bookid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(60), unique=True, nullable=False)
    author = db.Column(db.String(60), nullable=False)
    date_created = db.Column(
        db.Date, nullable=False, default=datetime.now(timezone.utc).date()
    )
    picture = db.Column(
        db.String(20), nullable=False, default="default_book_picture.png"
    )
    description = db.Column(db.String(120), nullable=False)
    pdf_file = db.Column(db.String(20), nullable=False)
    sectionid = db.Column(
        db.Integer, db.ForeignKey("section.sectionid"), nullable=False, default=1
    )
    section = db.relationship("Section", back_populates="books")
    issuedbooks = db.relationship(
        "IssuedBook", back_populates="book", lazy=True, cascade="all, delete-orphan"
    )
    feedbacks = db.relationship(
        "Feedback", back_populates="book", lazy=True, cascade="all, delete-orphan"
    )
    requests = db.relationship(
        "Request", back_populates="book", lazy=True, cascade="all, delete-orphan"
    )

    def __init__(
        self,
        title,
        author,
        picture,
        description,
        pdf_file="sample_pdf.pdf",
        sectionid=1,
        date_created=datetime.now(timezone.utc).date(),
    ):
        self.title = title
        self.author = author
        self.date_created = date_created
        self.picture = picture
        self.description = description
        self.pdf_file = pdf_file
        self.sectionid = sectionid

    def __repr__(self):
        return f"Book('{self.bookid}', '{self.title}', '{self.author}', '{self.date_created}', '{self.picture}', '{self.description}', '{self.pdf_file}', '{self.sectionid}')"


class Request(db.Model):
    __tablename__ = "request"
    requestid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey("user.userid"), nullable=False)
    date_created = db.Column(
        db.Date, nullable=False, default=datetime.now(timezone.utc).date()
    )
    days = db.Column(db.Integer, nullable=False)
    bookid = db.Column(db.Integer, db.ForeignKey("book.bookid"), nullable=False)
    status = db.Column(db.String(20), default="pending")
    user = db.relationship("User", back_populates="requests")
    book = db.relationship("Book", back_populates="requests")

    __table_args__ = (
        CheckConstraint("days >= 1 AND days <= 7", name="check_days"),
        CheckConstraint(
            status.in_(["pending", "accepted", "rejected"]), name="check_status"
        ),
    )

    def __init__(
        self,
        userid,
        days,
        bookid,
        status="pending",
        date_created=datetime.now(timezone.utc).date(),
    ):
        self.userid = userid
        self.date_created = date_created
        self.days = days
        self.bookid = bookid
        self.status = status

    def __repr__(self):
        return f"Request('{self.requestid}','{self.userid}', '{self.date_created}','{self.days}', '{self.bookid}', '{self.status}')"


class IssuedBook(db.Model):
    __tablename__ = "issuedbook"
    issueid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey("user.userid"), nullable=False)
    issued_by = db.Column(db.Integer, db.ForeignKey("user.userid"), nullable=False)
    bookid = db.Column(db.Integer, db.ForeignKey("book.bookid"), nullable=False)
    from_date = db.Column(
        db.Date, nullable=False, default=datetime.now(timezone.utc).date()
    )
    to_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="current")
    user = db.relationship("User", foreign_keys=[userid], back_populates="issuedbooks")
    issuer = db.relationship(
        "User", foreign_keys=[issued_by], back_populates="issued_books"
    )
    book = db.relationship("Book", back_populates="issuedbooks")

    __table_args__ = (
        CheckConstraint(status.in_(["current", "returned"]), name="check_status"),
    )

    def __init__(self, userid, issued_by, bookid, from_date, to_date, status="current"):
        self.userid = userid
        self.issued_by = issued_by
        self.bookid = bookid
        self.from_date = from_date
        self.to_date = to_date
        self.status = status

    def __repr__(self):
        return f"IssuedBook({self.issueid}', '{self.userid}', '{self.bookid}', '{self.from_date}', '{self.to_date}', '{self.status}')"


User.issuedbooks = db.relationship(
    "IssuedBook",
    foreign_keys="IssuedBook.userid",
    back_populates="user",
    lazy=True,
    cascade="all, delete-orphan",
)
User.issued_books = db.relationship(
    "IssuedBook",
    foreign_keys="IssuedBook.issued_by",
    back_populates="issuer",
    lazy=True,
    cascade="all, delete-orphan",
)


class Feedback(db.Model):
    __tablename__ = "feedback"
    feedbackid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey("user.userid"), nullable=False)
    bookid = db.Column(db.Integer, db.ForeignKey("book.bookid"), nullable=False)
    date_created = db.Column(
        db.Date, nullable=False, default=datetime.now(timezone.utc).date()
    )
    rating = db.Column(db.Integer, nullable=False)
    content = db.Column(db.String(200), nullable=False)
    user = db.relationship("User", back_populates="feedbacks")
    book = db.relationship("Book", back_populates="feedbacks")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating"),
    )

    def __init__(
        self,
        userid,
        bookid,
        rating,
        content,
        date_created=datetime.now(timezone.utc).date(),
    ):
        self.userid = userid
        self.bookid = bookid
        self.date_created = date_created
        self.rating = rating
        self.content = content

    def __repr__(self):
        return f"Feedback('{self.feedbackid}', '{self.userid}', '{self.bookid}', '{self.date_created}', '{self.rating}', '{self.content}')"
