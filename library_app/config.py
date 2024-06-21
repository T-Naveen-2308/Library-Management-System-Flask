import os
from dotenv import load_dotenv
from base64 import b64decode

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = os.environ.get("MAIL_PORT")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS")
    MAIL_USERNAME = b64decode(os.environ.get("MAIL_USERNAME")).decode("utf-8")
    MAIL_PASSWORD = b64decode(os.environ.get("MAIL_PASSWORD") + "==").decode("utf-8")