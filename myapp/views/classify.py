from flask import Blueprint
from flask_restful import Resource, Api, reqparse
from myapp.utils import db_conn_error_decorator, db_commit
from flask_jwt_extended import jwt_required
from myapp.models import Classify
from myapp import db

classify = Blueprint('classify_page', __name__, url_prefix='/classify')
api = Api(classify)

classify_parser = reqparse.RequestParser()
classify_parser.add_argument('category', type=str, required=True,
                             help='Category cannot be blank')


class ClassifyListCreateAPIView(Resource):
    method_decorators = [jwt_required, db_conn_error_decorator]

    def get(self):
        # 获取数据
        query = Classify.query
        count = query.count()
        classifys = query.all()

        return {
            'count': count,
            'results': [{
                'id': classify.id,
                'category': classify.category,
            } for classify in classifys]
        }

    def post(self):
        # 解析json数据
        args = classify_parser.parse_args()

        # 写入数据库
        classify = Classify(**args)

        db.session.add(classify)
        db_commit()

        return {
            'id': classify.id,
            'category': classify.category,
        }


api.add_resource(ClassifyListCreateAPIView, '/')
