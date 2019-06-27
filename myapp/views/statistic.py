from datetime import datetime, timedelta, date
from flask import Blueprint
from flask_restful import Resource, Api
from sqlalchemy import extract, and_, func, desc
from myapp.utils import db_conn_error_decorator
from flask_jwt_extended import jwt_required
from myapp.models import Scheduling, User, Shift, Classify, Ticket, Ticket_2_Server, Server
from myapp import db


statistic = Blueprint('statistic_page', __name__, url_prefix='/statistic')
api = Api(statistic)


class ClassifyStatistic(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        ### 本月故障分类统计
        today = datetime.now()
        year = today.year
        month = today.month

        query = db.session.query(
            Classify.category, func.count(Ticket.id))\
            .join(Ticket).filter(and_(
                extract('month', Ticket.occur_time) == month,
                extract('year', Ticket.occur_time) == year))\
            .group_by(Ticket.classify_id).all()

        return {
            'results': [{
                'category': q[0],
                'count': q[1],
            } for q in query]
        }


class LevelStatistic(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        ### 七天故障级别统计
        seven_days_ago = datetime.now() - timedelta(days=6)

        query = db.session.query(
            Ticket.level, func.date_format( Ticket.occur_time, '%d'). label('day'),
            func.count(Ticket.id)).filter(
            Ticket.occur_time > seven_days_ago).group_by(Ticket.level, 'day').all()

        results = {}
        for level, day, count in query:
            if not results.get(day):
                results[day] = {}
            results[day][level] = count

        return {
            'results': results
        }


class ServerStatistic(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        ### 本月故障服务器top7
        today = datetime.now()
        year = today.year
        month = today.month

        query = db.session.query(
            Server, func.count(Ticket_2_Server.id).label('count'))\
            .join(Ticket_2_Server).join(Ticket).filter(and_(
                extract('month', Ticket.occur_time) == month,
                extract('year', Ticket.occur_time) == year))\
            .group_by(Ticket_2_Server.server_id).order_by(desc('count')).limit(7).all()

        return {
            'results': [{
                'id': s.id,
                'hostname': s.hostname,
                'ip': s.ip,
                'count': count,
            } for s, count in query]
        }


class SchedulingTodayStatistic(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        ### 获取今天值班人员
        today = datetime.now().date()

        query = Scheduling.query.filter(Scheduling.date == today).all()

        return {
            'results': [{
                'id': s.id,
                'user': s.user.name,
                'start_time': s.shift.start_time.strftime("%H:%M:%S"),
                'end_time': s.shift.end_time.strftime("%H:%M:%S"),
            } for s in query]
        }


api.add_resource(ClassifyStatistic, '/classify')
api.add_resource(LevelStatistic, '/level')
api.add_resource(ServerStatistic, '/server')
api.add_resource(SchedulingTodayStatistic, '/scheduling')
