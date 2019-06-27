from flask import Blueprint
from flask_restful import Resource, Api, abort, reqparse, request
from myapp.utils import validate, db_conn_error_decorator, admin_required, send_mail, db_commit
from myapp.models import User
from myapp import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from random import choice
import string


user = Blueprint('user_page', __name__, url_prefix='/user')
api = Api(user)

user_parser = reqparse.RequestParser()
user_parser.add_argument('account', type=str, required=True,
                         help='Account cannot be blank')
user_parser.add_argument('name', type=str, required=True,
                         help='Name cannot be blank')
user_parser.add_argument('email', type=str, required=True,
                         help='Email cannot be blank')
user_parser.add_argument('is_super', type=int)
user_parser.add_argument('is_active', type=int)
user_parser.add_argument('phone', type=str)
user_parser.add_argument('remarks', type=str)


def gen_password(length: int = 10):
    return "".join([choice(string.ascii_letters + string.digits)
                    for _ in range(length)])


def send_password(user, passwd):
    send_mail("运维管理平台密码",
              "<h3>{} 您好:</h3><div>您的密码为: <b>{}</b></div>"
              .format(user.name, passwd), user.email)


class UserListCreateAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        # 分页
        page = validate(request.args, "page", int, 1,
                        lambda x, y: x if x > 0 else y)
        page_size = validate(request.args, "page_size", int, 10,
                             lambda x, y: x if 100 >= x >= 10 else y)

        name = request.args.get('name')

        # 获取数据
        query = User.query

        if name:
            query = query.filter(
                (User.name.like("%{}%".format(name))) | (User.account.like("%{}%".format(name))))

        count = query.count()
        users = query.limit(page_size).offset(page_size * (page - 1)).all()

        if 0 < count <= page_size * (page - 1):
            abort(404, message="Invalid page")

        return {
            'count': count,
            'page': page,
            'page_size': page_size,
            'results': [{
                'id': user.id,
                'account': user.account,
                'name': user.name,
                'is_super': user.is_super,
                'is_active': user.is_active,
                'email': user.email,
                'phone': user.phone,
                'remarks': user.remarks
            } for user in users]
        }

    @admin_required
    def post(self):
        # 解析json数据
        args = user_parser.parse_args()

        # 写入数据库
        user = User(**args)
        passwd = gen_password(10)
        user.set_password(passwd)

        db.session.add(user)
        db_commit()

        send_password(user, passwd)

        return {
            'id': user.id,
            'account': user.account,
            'name': user.name,
            'is_super': user.is_super,
            'is_active': user.is_active,
            'email': user.email,
            'phone': user.phone,
            'remarks': user.remarks
        }


class UserUpdateDestroyAPIView(Resource):
    method_decorators = [admin_required, jwt_required, db_conn_error_decorator]

    def put(self, user_id):
        # 修改用户
        # 解析json数据
        args = user_parser.parse_args()

        # 查找用户
        user = User.query.filter(User.id == user_id).first()
        if not user:
            abort(400, message="User does not exist")

        # 写入数据库
        user.update(**args)

        db.session.add(user)
        db_commit()

        return {
            'id': user.id,
            'account': user.account,
            'name': user.name,
            'is_super': user.is_super,
            'is_active': user.is_active,
            'email': user.email,
            'phone': user.phone,
            'remarks': user.remarks
        }

    def delete(self, user_id):
        # 查找用户
        user = User.query.filter(User.id == user_id).first()
        if not user:
            abort(400, message="User does not exist")

        db.session.delete(user)
        db_commit()

        return "", 204


class UserListsAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        # 获取数据
        name = request.args.get('name')
        query = User.query
        if name:
            query = query.filter(
                (User.name.like("%{}%".format(name))) | (User.account.like("%{}%".format(name))))
        else:
            return {
                'count': 0,
                'results': []
            }

        count = query.count()
        users = query.all()

        return {
            'count': count,
            'results': [{
                'id': user.id,
                'account': user.account,
                'name': user.name
            } for user in users]
        }


class UserInfoAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        # 解析jwt数据
        user_id = get_jwt_identity()

        # 获取用户
        user = User.query.filter(User.id == user_id).first()
        if not user:
            abort(400, message="User does not exist")

        return {
            'id': user.id,
            'account': user.account,
            'name': user.name,
            'is_super': user.is_super,
            'email': user.email,
            'phone': user.phone
        }


api.add_resource(UserListCreateAPIView, '/')
api.add_resource(UserUpdateDestroyAPIView, '/<int:user_id>')
api.add_resource(UserListsAPIView, '/list')
api.add_resource(UserInfoAPIView, '/info')
