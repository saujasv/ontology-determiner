from flask_sqlalchemy import SQLAlchemy
from onto_app import db

class users(db.Model):
    __tabelname__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    privilege = db.Column(db.Integer, nullable=False)
    ontology = db.relationship('ontologies', backref='users')
    decisions = db.relationship('decisions', backref='users')

class ontologies(db.Model):
    __tabelname__ = 'ontologies'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(200), unique=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    relations = db.relationship('relations', backref='ontologies')
    decisions = db.relationship('decisions', backref='ontologies')

class relations(db.Model):
    name = db.Column(db.String(200), nullable=False, primary_key=True)
    type = db.Column(db.String(200), nullable=False)
    domain_item = db.Column(db.String(200), nullable=False, primary_key=True)
    range_item = db.Column(db.String(200), nullable=False, primary_key=True)
    onto_id = db.Column(db.Integer, db.ForeignKey('ontologies.id'), nullable=False)
    decisions = db.relationship('decisions', backref='relations')

class decisions(db.Model):
    name = db.Column(db.String(200), db.ForeignKey('relations.name'), nullable=False, primary_key=True)
    domain_item = db.Column(db.String(200), db.ForeignKey('relations.domain_item'), nullable=False, primary_key=True)
    range_item = db.Column(db.String(200), db.ForeignKey('relations.range_item'), nullable=False, primary_key=True)
    onto_id = db.Column(db.Integer, db.ForeignKey('ontologies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

db.drop_all()
db.create_all()
