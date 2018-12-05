from flask_sqlalchemy import SQLAlchemy
from onto_app import db
from onto_app.onto import add_new_ontologies

class users(db.Model):
    __tabelname__ = 'users'
    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    # password = db.Column(db.String(200), nullable=False)
    privilege = db.Column(db.Integer, nullable=False)
    ontology = db.relationship('ontologies', backref='users')
    decisions = db.relationship('class_decisions', cascade="all,delete", backref='users')

class ontologies(db.Model):
    __tablename__ = 'ontologies'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    # filepath = db.Column(db.String(200), unique=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    relations = db.relationship('class_relations', cascade="all,delete", backref='ontologies')

class class_relations(db.Model):
    __tablename__ = 'class_relations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    property = db.Column(db.String(200))
    domain = db.Column(db.String(200), nullable=False)
    range = db.Column(db.String(200), nullable=False)
    quantifier = db.Column(db.String(200))
    onto_id = db.Column(db.Integer, db.ForeignKey('ontologies.id'), nullable=False)
    decisions = db.relationship('class_decisions', cascade="all,delete", backref='class_relations')

class class_decisions(db.Model):
    __tablename__ = 'class_decisions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    relation_id = db.Column(db.Integer, db.ForeignKey('class_relations.id'), nullable=False)
    approved = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class nodes(db.Model):
    __tablename__ = 'nodes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    onto_id = db.Column(db.Integer, db.ForeignKey('ontologies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    decisions = db.relationship('node_decisions', cascade="all,delete", backref='nodes')

class node_decisions(db.Model):
    __tablename__ = 'node_decisions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    node_id = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=False)
    approved = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# db.drop_all()
try:
    db.create_all()
except:
    pass

