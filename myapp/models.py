from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint
from myapp import db
import bcrypt


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.String(24), nullable=False, unique=True)
    name = db.Column(db.String(24), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    is_super = db.Column(db.Boolean, nullable=False, default=False,
                         comment="False-普通用户、True-管理员")
    is_active = db.Column(db.Boolean, nullable=False, default=True,
                          comment="False-禁用、True-启用")
    email = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(24))
    remarks = db.Column(db.String(256))

    def __repr__(self):
        return '<User {}>'.format(self.name)

    def set_password(self, password):
        self.password = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password.encode())

    def update(self, **validate):
        self.account = validate['account']
        self.name = validate['name']
        self.is_super = validate['is_super']
        self.is_active = validate['is_active']
        self.email = validate['email']
        self.phone = validate['phone']
        self.remarks = validate['remarks']


class Ticket(db.Model):
    __tablename__ = 'ticket'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(128), nullable=False)
    pub_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.TEXT, nullable=False)
    affect = db.Column(db.TEXT, nullable=False)
    pub_user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            nullable=False)
    handler_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            nullable=False)
    status = db.Column(db.SmallInteger, nullable=False, default=0,
                       comment="0-未处理、1-处理中、2-已解决、3-挂起")
    level = db.Column(db.SmallInteger, nullable=False,
                      comment="1-一般、2-严重、3-重大")
    classify_id = db.Column(db.Integer, db.ForeignKey(
        'classify.id'), nullable=False)
    occur_time = db.Column(db.DateTime, nullable=False)
    restore_time = db.Column(db.DateTime)

    classify = relationship("Classify")
    pub_user = relationship("User", foreign_keys=[pub_user_id])
    handler = relationship("User", foreign_keys=[handler_id])
    progresses = relationship("Progress")

    def __repr__(self):
        return '<Ticket {}>'.format(self.title)

    __mapper_args__ = {
        "order_by": pub_time.desc()
    }


class Server(db.Model):
    __tablename__ = 'server'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hostname = db.Column(db.String(64), nullable=False, unique=True)
    ip = db.Column(db.String(64), nullable=False, unique=True)
    app = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False)
    remarks = db.Column(db.String(256))

    user = relationship("User")

    def __repr__(self):
        return '<Server {}>'.format(self.hostname)

    def update(self, **validate):
        self.hostname = validate['hostname']
        self.ip = validate['ip']
        self.app = validate['app']
        self.user_id = validate['user_id']
        self.remarks = validate['remarks']


class Ticket_2_Server(db.Model):
    __tablename__ = 'ticket_2_server'
    __table_args__ = (UniqueConstraint("ticket_id", "server_id"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'),
                          nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey('server.id'),
                          nullable=False)

    ticket = relationship("Ticket")
    server = relationship("Server")


class Classify(db.Model):
    __tablename__ = 'classify'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return '<Classify {}>'.format(self.category)

    def update(self, **validate):
        self.category = validate['category']


class Progress(db.Model):
    __tablename__ = 'progress'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    handle_time = db.Column(db.DateTime, nullable=False)
    handler_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                           nullable=False)
    progress = db.Column(db.TEXT, nullable=False)
    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey('ticket.id'),
        nullable=False)

    handler = relationship("User")

    def __repr__(self):
        return '<Progress {}>'.format(self.id)

    __mapper_args__ = {
        "order_by": handle_time
    }


class Scheduling(db.Model):
    __tablename__ = 'scheduling'
    __table_args__ = (UniqueConstraint("date", "user_id"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.id'), nullable=False)

    user = relationship('User')
    shift = relationship('Shift')

    def __repr__(self):
        return '<Scheduling {}>'.format(self.id)


class Shift(db.Model):
    __tablename__ = 'shift'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shift = db.Column(db.CHAR(2), nullable=False, unique=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    __mapper_args__ = {
        "order_by": shift
    }

    def update(self, **validate):
        self.shift = validate['shift']
        self.start_time = validate['start_time']
        self.end_time = validate['end_time']


