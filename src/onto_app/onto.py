import subprocess

from onto_app import db
from onto_app.aggregate import aggregate
from rdflib import Graph
from rdflib.namespace import OWL, RDF, RDFS

OWL2VOWL = 'OWL2VOWL-0.3.5-shaded.jar'

def is_blank(node):
    if not '#' in node:
        return True
    else:
        return False

def add_onto_file(admin_id, name, filepath, json_path, new_relations_file):
    # compile OWL to JSON using OWL2VOWL
    f = open(json_path, 'w')
    try:
        subprocess.run(['java', '-jar', OWL2VOWL, '-file', filepath, '-echo'], stdout=f)
    except:
        raise RuntimeError

    # Create record for ontology in database
    insert_query = """INSERT INTO ontologies (name, filepath, admin_id)
                        VALUES (:name, :filepath, :admin_id)"""
    result = db.engine.execute(insert_query, {'name': name, 'filepath': filepath, 'admin_id': admin_id})
    new_ontology_id = result.lastrowid

    # add new relations to database
    new_relations = get_new_relations(new_relations_file)
    add_relations_to_db(new_relations, new_ontology_id)

def get_new_relations(filepath):
    d = dict()
    f = open(filepath, 'r')
    relations = list()

    # Each line of the new relations file is an RDF triple, so it is a
    # triple of the subject, predicate, and object
    # Create an adjacency list graph from the triples
    for l in f.readlines():
        s, p, o = l.split()
        if s in d:
            d[s].append((p, o))
        else:
            d[s] = [(p, o)]

    # From the graph, find all restricitons (blank nodes) and get the relevant
    # relation data from them
    for s in d:
        if not is_blank(s):
            for p, o in d[s]:
                if is_blank(o):
                    domain = s
                    rang = None
                    quant = None
                    prop = None
                    for p1, o1 in d[o]:
                        if p1 == str(OWL.onProperty):
                            prop = o1
                        elif p1 == str(OWL.someValuesFrom):
                            quant = p1
                            rang = o1
                    if quant == str(OWL.someValuesFrom):
                        relations.append((domain, prop, quant, rang))

    return relations

def add_relations_to_db(relations, onto_id):
    insert_query = """INSERT INTO
                    class_relations (domain, property, quantifier, range, onto_id)
                    VALUES (:domain, :property, :quantifier, :range, :onto_id)"""
    args = {'domain': None, 'property': None, 'quantifier': None, 'range': None, 'onto_id': onto_id}
    print("#relations = ", len(relations))
    for r in relations:
        args['domain'] = r[0]
        args['property'] = r[1]
        args['quantifier'] = r[2]
        args['range'] = r[3]
        result = db.engine.execute(insert_query, args)

def add_decision(user_id, property, domain, range, quantifier, onto_id, decision):
    relation_query = """SELECT id FROM class_relations
                        WHERE onto_id = :onto_id
                            AND property = :property
                            AND domain = :domain
                            AND range = :range"""

    result = db.engine.execute(relation_query, {
        'onto_id': onto_id,
        'property': property,
        'domain': domain,
        'range': range
        # 'quantifier': quantifier
    })

    relation_id = result.fetchone()['id']

    insert_query = """INSERT INTO class_decisions
                        (relation_id, user_id, approved)
                        VALUES (:relation_id, :user_id, :approved)"""
    result = db.engine.execute(insert_query, {
        'relation_id': relation_id,
        'user_id': user_id,
        'approved': decision
    })

def get_decision(relation_id):
    query = """SELECT * FROM class_decisions WHERE relation_id = :relation_id"""
    result = db.engine.execute(query, {'relation_id': relation_id})
    return aggregate(result.fetchall())
