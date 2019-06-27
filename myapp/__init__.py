from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()


def create_app(*config_obj):
    app = Flask(__name__)

    for obj in config_obj:
        app.config.from_object(obj)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    from myapp.views.server import server
    from myapp.views.user import user
    from myapp.views.auth import auth
    from myapp.views.scheduling import scheduling
    from myapp.views.classify import classify
    from myapp.views.ticket import ticket
    from myapp.views.shift import shift
    from myapp.views.statistic import statistic
    app.register_blueprint(server)
    app.register_blueprint(user)
    app.register_blueprint(auth)
    app.register_blueprint(scheduling)
    app.register_blueprint(classify)
    app.register_blueprint(ticket)
    app.register_blueprint(shift)
    app.register_blueprint(statistic)

    return app
