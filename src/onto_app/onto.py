from owlready2 import *
from onto_app import db
import os

def add_onto_file(admin_id, name, filepath, json_path):
    # TODO
    # add record of ontology to database
    db.engine.execute("INSERT INTO ontologies (name, filepath, admin_id) VALUES (:name, :filepath, :admin_id)", {'name': name, 'filepath': filepath, 'admin_id': admin_id})
    os.system("java -jar " + os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/data/json/OWL2VOWL-0.3.5-shaded.jar')+ " -file " + filepath + " -echo >> " + json_path)
    # open and load ontology, get relations and annotations
    # add relations to db

def get_relations(onto):
    pass
    # TODO

def add_relations_to_db(relations):
    pass
    # TODO

def add_decision(user_id, name, type):
    pass
    # TODO
