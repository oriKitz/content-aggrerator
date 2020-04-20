from aggregator import db
import datetime
from sqlalchemy.inspection import inspect


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
