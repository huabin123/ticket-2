import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(
        os.path.join(BASE_DIR, "db.sqlite3"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = "GIAQpBwBDVr6QNI5y5ku"
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60
    JWT_HEADER_TYPE = "JWT"
    JWT_ERROR_MESSAGE_KEY = "message"

    MAIL_SERVER = "smtp.qq.com"
    MAIL_PORT = "587"
    MAIL_USE_TLS = True
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = ""


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://ops:ops@127.0.0.1:3306/ops'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://ops:ops@127.0.0.1:3306/ops'
    SQLALCHEMY_ECHO = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
