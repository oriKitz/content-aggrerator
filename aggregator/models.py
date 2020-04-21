from aggregator import db, login_manager
import datetime
from sqlalchemy.inspection import inspect
from flask_login import UserMixin


class NewsItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website = db.Column(db.String(20), nullable=False)
    headline = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(400))
    link = db.Column(db.String, unique=True, nullable=False)
    publish_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)

    def __repr__(self):
        return f'{self.website}: {self.headline} at {self.publish_time}'

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"'{self.username}', '{self.email}'"
