from myapp import db, mail
from flask_restful import abort
from functools import wraps
from sqlalchemy import exc
from flask_jwt_extended import get_jwt_identity
from .models import User
from flask_mail import Message


def validate(d: dict, name: str, type_func, default, func):
    try:
        result = type_func(d.get(name, default))
        result = func(result, default)
    except:
        result = default
    return result


def db_conn_error_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except exc.OperationalError as e:
            db.session.rollback()
            abort(500, message="Internal Server Error")
        return ret
    return wrapper


def db_commit():
    try:
        db.session.commit()
    except exc.IntegrityError as e:
        db.session.rollback()
        abort(409, message="Integrity Error")
    except Exception as e:
        db.session.rollback()
        abort(500, message="Internal Server Error")


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 解析jwt数据
        user_id = get_jwt_identity()
        # 获取用户
        user = User.query.filter(User.id == user_id).first()

        if not user.is_super:
            abort(403, message="Permission denied")

        return func(*args, **kwargs)
    return wrapper


def send_mail(subject, html, *recipients):
    msg = Message()
    msg.recipients = list(recipients)
    msg.subject = subject
    msg.html = html
    try:
        mail.send(msg)
        return True
    except Exception as e:
        return False
