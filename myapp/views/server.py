from flask import Blueprint
from flask_restful import Resource, Api, abort, reqparse, request
from myapp.utils import validate, db_conn_error_decorator, admin_required, db_commit
from flask_jwt_extended import jwt_required
from myapp.models import Server
from myapp import db

server = Blueprint('server_page', __name__, url_prefix='/server')
api = Api(server)


server_parser = reqparse.RequestParser()
server_parser.add_argument('hostname', type=str, required=True,
                         help='Hostname cannot be blank')
server_parser.add_argument('ip', type=str, required=True,
                         help='IP cannot be blank')
server_parser.add_argument('app', type=str, required=True,
                         help='App cannot be blank')
server_parser.add_argument('user_id', type=int, required=True,
                         help='User_id cannot be blank')
server_parser.add_argument('remarks', type=str)


class ServerListCreateAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        # 分页
        page = validate(request.args, "page", int, 1,
                        lambda x, y: x if x > 0 else y)
        page_size = validate(request.args, "page_size", int, 10,
                             lambda x, y: x if 100 >= x >= 10 else y)

        # 获取数据
        name = request.args.get('name')

        # 获取数据
        query = Server.query

        if name:
            query = query.filter((Server.hostname.like("%{}%".format(name))) | (Server.ip.like("%{}%".format(name))))

        count = query.count()
        servers = query.limit(page_size).offset(page_size * (page - 1)).all()

        if 0 < count <= page_size * (page - 1):
            abort(404, message="Invalid page")

        return {
            'count': count,
            'page': page,
            'page_size': page_size,
            'results': [{
                'id': server.id,
                'hostname': server.hostname,
                'ip': server.ip,
                'app': server.app,
                'user': {
                    'id': server.user.id,
                    'name': server.user.name,
                    'account': server.user.account,
                },
                'remarks': server.remarks
            } for server in servers]
        }

    @admin_required
    def post(self):
        # 解析json数据
        args = server_parser.parse_args()

        # 写入数据库
        server = Server(**args)

        db.session.add(server)
        db_commit()

        return {
            'id': server.id,
            'hostname': server.hostname,
            'ip': server.ip,
            'app': server.app,
            'user': server.user.name,
            'remarks': server.remarks
        }


class ServerUpdateDestroyAPIView(Resource):
    method_decorators = [admin_required, jwt_required, db_conn_error_decorator]

    def put(self, server_id):
        # 解析json数据
        args = server_parser.parse_args()

        # 查找服务器
        server = Server.query.filter(Server.id == server_id).first()
        if not server:
            abort(400, message="Server does not exist")

        # 写入数据库
        server.update(**args)

        db.session.add(server)
        db_commit()

        return {
            'id': server.id,
            'hostname': server.hostname,
            'ip': server.ip,
            'app': server.app,
            'user': server.user.name,
            'remarks': server.remarks
        }

    def delete(self, server_id):
        server = Server.query.filter(Server.id == server_id).first()
        if not server:
            abort(400, message="Server does not exist")

        db.session.delete(server)
        db_commit()

        return "", 204


class ServerListsAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        # 获取数据
        name = request.args.get('name')
        query = Server.query
        if name:
            query = query.filter((Server.hostname.like("%{}%".format(name))) | (Server.ip.like("%{}%".format(name))))
        else:
            return {
                'count': 0,
                'results': []
            }

        count = query.count()
        servers = query.all()

        return {
            'count': count,
            'results': [{
                'id': server.id,
                'hostname': server.hostname,
                'ip': server.ip
            } for server in servers]
        }


api.add_resource(ServerListCreateAPIView, '/')
api.add_resource(ServerUpdateDestroyAPIView, '/<int:server_id>')
api.add_resource(ServerListsAPIView, '/list')
