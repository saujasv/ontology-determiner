import os

from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(Config)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'onto.db')

db = SQLAlchemy(app)

from onto_app import routes, models
from onto_app.onto import *

# add_new_ontologies()
#add_onto_file(0, 'pizza', os.path.abspath(os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/data/owl/pizza.owl')), os.path.abspath(os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/data/json/pizza.json')))
