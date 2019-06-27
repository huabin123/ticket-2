from datetime import datetime
from flask import Blueprint
from flask_restful import Resource, Api, abort, reqparse, request
from myapp.utils import db_conn_error_decorator, validate, db_commit
from flask_jwt_extended import jwt_required, get_jwt_identity
from myapp.models import Ticket, Server, Ticket_2_Server, Progress, User
from myapp import db

ticket = Blueprint(
    'ticket_page',
    __name__,
    url_prefix='/ticket')
api = Api(ticket)


class TicketListCreateAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    parser = reqparse.RequestParser()
    parser.add_argument('title', type=str, required=True,
                        help='Title cannot be blank')
    parser.add_argument('description', type=str, required=True,
                        help='Description cannot be blank')
    parser.add_argument('affect', type=str, required=True,
                        help='Affect cannot be blank')
    parser.add_argument('level', type=int, required=True,
                        help='Level cannot be blank')
    parser.add_argument('handler_id', type=int, required=True,
                        help='Handler_id cannot be blank')
    parser.add_argument('classify_id', type=int, required=True,
                        help='Classify_id cannot be blank')
    parser.add_argument('occur_time', type=str, required=True,
                        help='Occur_time cannot be blank')
    parser.add_argument('servers', type=int, action='append',
                        required=True,
                        help='Servers cannot be blank')

    def get(self):
        # 分页
        page = validate(request.args, "page", int, 1,
                        lambda x, y: x if x > 0 else y)

        page_size = validate(request.args, "page_size", int, 10,
                             lambda x, y: x if 100 >= x >= 10 else y)

        status = validate(request.args, "status", int, -1,
                          lambda x, y: x if 3 >= x >= 0 else y)

        level = validate(request.args, "level", int, 0,
                         lambda x, y: x if 3 >= x >= 1 else y)

        user = request.args.get('user')
        title = request.args.get('title')
        start = request.args.get('start')
        end = request.args.get('end')

        # 获取数据
        query = Ticket.query

        # 获取指定状态的故障单
        if user:
            query = query.filter(Ticket.handler_id == user)

        if status != -1:
            query = query.filter(Ticket.status == status)

        if level:
            query = query.filter(Ticket.level == level)

        if start and end:
            query = query.filter(Ticket.occur_time.between(start, end))

        if title:
            query = query.filter(Ticket.title.like("%{}%".format(title)))

        count = query.count()
        tickets = query.limit(page_size).offset(
            page_size * (page - 1)).all()

        if 0 < count <= page_size * (page - 1):
            abort(404, message="Invalid page")

        return {
            'count': count,
            'page': page,
            'page_size': page_size,
            'results': [{
                'id': ticket.id,
                'title': ticket.title,
                'level': ticket.level,
                'status': ticket.status,
                'handler': ticket.handler.name,
                'classify': ticket.classify.category,
                'occur_time': ticket.occur_time.strftime("%Y-%m-%d %H:%M:%S"),
                'restore_time':
                    ticket.restore_time.strftime("%Y-%m-%d %H:%M:%S") if ticket.restore_time else None,
            } for ticket in tickets]
        }

    def post(self):
        args = self.parser.parse_args()
        servers = args.pop('servers')

        # 写入数据库
        ticket = Ticket(**args)
        ticket.pub_time = datetime.now()
        ticket.pub_user_id = get_jwt_identity()

        for server_id in servers:
            server = Server.query.filter(Server.id == server_id).first()
            if server:
                t2s = Ticket_2_Server()
                t2s.server = server
                t2s.ticket = ticket
                db.session.add(t2s)
            else:
                abort(400, message="Server does not exist")

        db.session.add(ticket)
        db_commit()

        return {
            'id': ticket.id,
            'title': ticket.title,
            'pub_time': ticket.pub_time.strftime("%Y-%m-%d %H:%M:%S"),
            'description': ticket.description,
            'affect': ticket.affect,
            'pub_user': ticket.pub_user.name,
            'handler': ticket.handler.name,
            'status': ticket.status,
            'level': ticket.level,
            'classify': ticket.classify.category,
            'occur_time': ticket.occur_time.strftime("%Y-%m-%d %H:%M:%S")
        }


class TicketUpdateDestroyAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    parser = reqparse.RequestParser()
    parser.add_argument('progress', type=str, required=True,
                        help='Progress cannot be blank')
    parser.add_argument('status', type=int, required=True,
                        help='Status cannot be blank')
    parser.add_argument('restore_time', type=str)

    def get(self, ticket_id):
        ticket = Ticket.query.filter(
            Ticket.id == ticket_id).first()
        if not ticket:
            abort(400, message="Ticket does not exist")

        servers = Server.query.join(Ticket_2_Server).filter(
            Ticket_2_Server.ticket_id == ticket.id).all()

        progresses = ticket.progresses

        return {
            'id': ticket.id,
            'title': ticket.title,
            'pub_time': ticket.pub_time.strftime("%Y-%m-%d %H:%M:%S"),
            'description': ticket.description,
            'affect': ticket.affect,
            'pub_user': ticket.pub_user.name,
            'handler': ticket.handler.name,
            'status': ticket.status,
            'level': ticket.level,
            'classify': ticket.classify.category,
            'occur_time': ticket.occur_time.strftime("%Y-%m-%d %H:%M:%S"),
            'restore_time':
                ticket.restore_time.strftime("%Y-%m-%d %H:%M:%S") if ticket.restore_time else None,
            'servers': [{
                'id': s.id,
                'hostname': s.hostname,
                'ip': s.ip,
                'app': s.app,
                'user': s.user.name,
            }for s in servers],
            'progresses': [{
                'id': p.id,
                'handle_time': p.handle_time.strftime("%Y-%m-%d %H:%M:%S"),
                'handler': p.handler.name,
                'progress': p.progress
            }for p in progresses]
        }

    def post(self, ticket_id):
        ticket = Ticket.query.filter(
            Ticket.id == ticket_id).first()
        if not ticket:
            abort(400, message="Ticket does not exist")

        if ticket.status == 2:
            abort(400, message="The fault has been resolved")

        args = self.parser.parse_args()
        progress = Progress()
        progress.handle_time = datetime.now()
        progress.handler_id = get_jwt_identity()
        progress.ticket_id = ticket_id
        progress.progress = args["progress"]

        if args["status"] in [1, 2, 3]:
            ticket.status = args["status"]
            if args["status"] == 2:
                if not args["restore_time"]:
                    abort(400, message="Restore_time cannot be blank")
                ticket.restore_time = args["restore_time"]
        else:
            abort(400, message="Status value error")

        db.session.add(ticket)
        db.session.add(progress)
        db_commit()

        return {
            'id': progress.id,
            'handle_time': progress.handle_time.strftime("%Y-%m-%d %H:%M:%S"),
            'handler': progress.handler.name,
            'progress': progress.progress,
            'ticket_id': progress.ticket_id
        }


class TicketHandlerUpdateAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    parser = reqparse.RequestParser()
    parser.add_argument('user_id', type=int, required=True,
                        help='User_id cannot be blank')
    parser.add_argument('tickets_id', type=str, required=True, action='append',
                        help='ID cannot be blank')

    def post(self):
        args = self.parser.parse_args()

        tickets = []
        for t_id in args["tickets_id"]:
            ticket = Ticket.query.filter(
                Ticket.id == t_id).first()
            if not ticket:
                abort(400, message="Ticket does not exist")

            if ticket.status == 2:
                continue

            tickets.append(ticket)

        target_user = User.query.filter(User.id == args['user_id']).first()
        if not target_user:
            abort(400, message="Bad Request")

        for t in tickets:
            t.handler = target_user

            progress = Progress()
            progress.handle_time = datetime.now()
            progress.handler_id = get_jwt_identity()
            progress.ticket_id = t.id
            progress.progress = "指定 [{}] 处理".format(target_user.name)

            db.session.add(t)
            db.session.add(progress)

        db_commit()

        return "", 200



api.add_resource(TicketListCreateAPIView, '/')
api.add_resource(TicketUpdateDestroyAPIView, '/<int:ticket_id>')
api.add_resource(TicketHandlerUpdateAPIView, '/assign')
