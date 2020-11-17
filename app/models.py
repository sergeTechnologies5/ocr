from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    national_id = db.Column(db.String(120), index=True, unique=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    number_plate = db.Column(db.String(140), index=True, unique=True)
    phone_number = db.Column(db.String(140), default='254708094707')
    checkins = db.relationship('Checkin', backref='vehicle', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.name)   

class Checkin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number_plate = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    timestamp_check_out = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    checkin_status = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Checkin {} {} {} >'.format(self.number_plate,self.user_id,self.timestamp)