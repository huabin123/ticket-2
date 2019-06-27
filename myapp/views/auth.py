from flask import Blueprint
from flask_restful import Resource, Api, abort, reqparse
from myapp.utils import db_conn_error_decorator
from myapp.models import User
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)

auth = Blueprint('auth_page', __name__, url_prefix='/auth')
api = Api(auth)


class AuthAPIView(Resource):
    method_decorators = [db_conn_error_decorator]

    parser = reqparse.RequestParser()
    parser.add_argument('account', type=str, required=True,
                        help='Account cannot be blank')
    parser.add_argument('password', type=str, required=True,
                        help='Password cannot be blank')

    def post(self):
        # 获取账号密码
        args = self.parser.parse_args()

        # 校验账号密码
        user = User.query.filter(User.account == args["account"]).first()
        if not user or not user.check_password(args["password"]):
            abort(400, msg="Incorrect account or password")

        if not user.is_active:
            abort(400, msg="Account is disabled")

        token = create_access_token(identity=user.id, fresh=True)

        return {'token': token}

    @jwt_required
    def get(self):
        # 刷新token
        user_id = get_jwt_identity()
        new_token = create_access_token(identity=user_id, fresh=False)
        return {'token': new_token}


api.add_resource(AuthAPIView, '/')
