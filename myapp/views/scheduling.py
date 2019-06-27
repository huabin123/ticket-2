import calendar
from datetime import datetime, date
from flask import Blueprint
from flask_restful import Resource, Api, abort, request
from sqlalchemy import extract, and_
from myapp.utils import db_conn_error_decorator, admin_required, validate, db_commit
from flask_jwt_extended import jwt_required
from myapp.models import Scheduling, User, Shift
from myapp import db
import xlrd


scheduling = Blueprint('scheduling_page', __name__, url_prefix='/scheduling')
api = Api(scheduling)


class SchedulingListCreateAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        today = datetime.now()
        current_month = today.year
        current_year = today.month
        month = validate(request.args, "month", int, current_month,
                         lambda x, y: x if 12 >= x >= 1 else y)
        year = validate(request.args, "year", int, current_year,
                        lambda x, y: x if x > 2018 else y)
        user = request.args.get('user')

        # 获取数据
        query = Scheduling.query
        if user:
            query = query.filter(Scheduling.user_id == user)

        query = query.filter(and_(
            extract('month', Scheduling.date) == month,
            extract('year', Scheduling.date) == year))

        schedulings = query.all()

        res = {}
        for s in schedulings:
            if not res.get(s.user.name):
                res[s.user.name] = {'user': s.user.name}
                res[s.user.name]["id"] = s.user.id
            res[s.user.name][s.date.day] = s.shift.shift

        return {
            'results': list(res.values())
        }

    @admin_required
    def post(self):
        try:
            file = request.files['file']
            year = int(request.form['year'])
            month = int(request.form['month'])
            if year < 2018 or not 0 < month < 13:
                abort(400, message="Bad Request")

            days = calendar.monthrange(year, month)[1]
            #
            query = Scheduling.query.filter(and_(
                extract('month', Scheduling.date) == month,
                extract('year', Scheduling.date) == year))
            #

            f = file.read()
            data = xlrd.open_workbook(file_contents=f)
            table = data.sheets()[0]

            users = set()
            for i in range(1, table.nrows):
                row_values = table.row_values(i)
                user = User.query.filter(
                    User.name == row_values[0]).first()
                if not user:
                    abort(400, message="Bad Request")

                users.add(user.id)

                for d in range(1, days + 1):
                    day = date(year, month, d)
                    try:
                        v = row_values[d]
                    except IndexError:
                        v = "休"

                    scheduling = query.filter(
                        (Scheduling.date == day) & (
                            Scheduling.user_id == user.id)).first()
                    shift = Shift.query.filter(Shift.shift == v).first()
                    if shift:
                        if scheduling:
                            scheduling.shift = shift
                        else:
                            scheduling = Scheduling(
                                user=user, date=day, shift=shift)
                        db.session.add(scheduling)
                    else:
                        if scheduling:
                            db.session.delete(scheduling)

            # 删除未排班用户
            for s in query.filter(~Scheduling.user_id.in_(users)):
                db.session.delete(s)

            db_commit()
        except Exception as e:
            abort(400, message="Bad Request")

        return "", 202


api.add_resource(SchedulingListCreateAPIView, '/')
