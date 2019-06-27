from flask import Blueprint
from flask_restful import Resource, Api, abort, reqparse
from myapp.utils import db_conn_error_decorator, admin_required, db_commit
from flask_jwt_extended import jwt_required
from myapp.models import Shift
from myapp import db

shift = Blueprint('shift_page', __name__, url_prefix='/shift')
api = Api(shift)

shift_parser = reqparse.RequestParser()
shift_parser.add_argument('shift', type=str, required=True,
                             help='Shift cannot be blank')
shift_parser.add_argument('start_time', type=str, required=True,
                             help='Start_time cannot be blank')
shift_parser.add_argument('end_time', type=str, required=True,
                             help='End_time cannot be blank')


class ShiftListCreateAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        # 获取数据
        query = Shift.query
        count = query.count()
        shifts = query.all()

        return {
            'count': count,
            'results': [{
                'id': shift.id,
                'shift': shift.shift,
                'start_time': shift.start_time.strftime("%H:%M:%S"),
                'end_time': shift.end_time.strftime("%H:%M:%S"),
            } for shift in shifts]
        }

    @admin_required
    def post(self):
        # 解析json数据
        args = shift_parser.parse_args()

        # 写入数据库
        shift = Shift(**args)

        db.session.add(shift)
        db_commit()

        return {
            'id': shift.id,
            'shift': shift.shift,
            'start_time': shift.start_time.strftime("%H:%M:%S"),
            'end_time': shift.end_time.strftime("%H:%M:%S"),
        }


class ShiftUpdateDestroyAPIView(Resource):
    method_decorators = [admin_required, jwt_required, db_conn_error_decorator]

    def put(self, shift_id):
        # 解析json数据
        args = shift_parser.parse_args()

        # 查找服务器
        shift = Shift.query.filter(Shift.id == shift_id).first()
        if not shift:
            abort(400, message="Shift does not exist")

        # 写入数据库
        shift.update(**args)

        db.session.add(shift)
        db_commit()

        return {
            'id': shift.id,
            'shift': shift.shift,
            'start_time': shift.start_time.strftime("%H:%M:%S"),
            'end_time': shift.end_time.strftime("%H:%M:%S"),
        }

    def delete(self, shift_id):
        shift = Shift.query.filter(Shift.id == shift_id).first()
        if not shift:
            abort(400, message="Shift does not exist")

        db.session.delete(shift)
        db_commit()

        return "", 204


api.add_resource(ShiftListCreateAPIView, '/')
api.add_resource(ShiftUpdateDestroyAPIView, '/<int:shift_id>')
