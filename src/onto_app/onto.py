import subprocess
from os import listdir
from os.path import isfile, join

from onto_app import db
# from onto_app.aggregate import accepted
from rdflib import Graph
from rdflib.namespace import OWL, RDF, RDFS

OWL2VOWL = 'OWL2VOWL-0.3.5-shaded.jar'

def is_blank(node):
    if not '#' in node:
        return True
    else:
        return False

def add_onto_file(admin_id, name):
    # compile OWL to JSON using OWL2VOWL
    json_path = './data/json/' + str(name) + '.json'
    new_relations_file = './data/new/' + str(name) + '.txt'
    filepath = './data/owl/'+str(name) + '.owl'
    f = open(json_path, 'w')
    try:
        subprocess.run(['java', '-jar', OWL2VOWL, '-file', filepath, '-echo'], stdout=f)
    except:
        raise RuntimeError

    # Create record for ontology in database
    insert_query = """INSERT INTO ontologies (name, admin_id)
                        VALUES (:name, :admin_id)"""
    result = db.engine.execute(insert_query, {'name': str(name), 'admin_id': admin_id})#'filepath': filepath, )
    new_ontology_id = result.lastrowid
    db.session.commit()

    # add new relations to database
    new_relations, new_nodes, new_subclasses = get_new_relations(new_relations_file)
    add_relations_to_db(new_relations, new_ontology_id)
    add_nodes_to_db(new_nodes, new_ontology_id)
    add_subclasses_to_db(new_subclasses, new_ontology_id)

def add_new_ontologies():
    ontologies = ['.'.join(f.split('.')[:-1]) for f in listdir("./data/owl/") if isfile(join("./data/owl/", f))]
    # print("Onto=", ontologies)
    result = db.engine.execute("""SELECT name FROM ontologies""")
    db_ontologies = [o['name'] for o in result.fetchall()]
    # print("DB=", db_ontologies)
    for onto in ontologies:
        # print(onto)
        if not (onto in db_ontologies):
            add_onto_file(0, onto)

def get_new_relations(filepath):
    d = dict()
    f = open(filepath, 'r')
    relations = list()
    classes = list()
    subclasses = list()

    # Each line of the new relations file is an RDF triple, so it is a
    # triple of the subject, predicate, and object
    # Create an adjacency list graph from the triples
    for l in f.readlines():
        s, p, o = l.split()
        if o == str(OWL.Class):
            classes.append(s)
        elif (p == str(RDFS.subClassOf) and not is_blank(s) and not is_blank(o)):
            subclasses.append((s, o))
        else:
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
    # print(subclasses)
    return relations, classes, subclasses

def add_nodes_to_db(nodes, onto_id):
    insert_query = """INSERT INTO
                    nodes (name, onto_id)
                    VALUES (:name, :onto_id)"""
    args = {'name': None, 'onto_id': onto_id}
    for n in nodes:
        args['name'] = n
        result = db.engine.execute(insert_query, args)
        # print(result)
    # db.session.commit()

def add_relations_to_db(relations, onto_id):
    insert_query = """INSERT INTO
                    class_relations (domain, property, quantifier, range, onto_id)
                    VALUES (:domain, :property, :quantifier, :range, :onto_id)"""
    args = {'domain': None, 'property': None, 'quantifier': None, 'range': None, 'onto_id': onto_id}
    # print("#relations = ", len(relations))
    for r in relations:
        args['domain'] = r[0]
        args['property'] = r[1]
        args['quantifier'] = r[2]
        args['range'] = r[3]
        result = db.engine.execute(insert_query, args)
        # print(result)
    # db.session.commit()

def add_subclasses_to_db(subclasses, onto_id):
    insert_query = """INSERT INTO
                    class_relations (domain, property, quantifier, range, onto_id)
                    VALUES (:domain, :property, :quantifier, :range, :onto_id)"""
    args = {'domain': None, 'property': None, 'quantifier': None, 'range': None, 'onto_id': onto_id}
    # print("#relations = ", len(relations))
    for r in subclasses:
        args['domain'] = r[0]
        args['property'] = None
        args['quantifier'] = str(RDFS.subClassOf)
        args['range'] = r[1]
        result = db.engine.execute(insert_query, args)
        # print(result)
    # db.session.commit()


def add_relation_decision(user_id, property, domain, range, quantifier, onto_id, decision):
    args = {
        'onto_id': onto_id,
        # 'property': property,
        'domain': domain,
        'range': range
        # 'quantifier': quantifier
    }
    if property:
        args['property'] = property
        relation_query = """SELECT id FROM class_relations
                        WHERE onto_id = :onto_id
                            AND property = :property
                            AND domain = :domain
                            AND range = :range"""
    else:
        relation_query = """SELECT id FROM class_relations
                        WHERE onto_id = :onto_id
                            AND domain = :domain
                            AND range = :range"""

    result = db.engine.execute(relation_query, args)

    relation_id = result.fetchone()['id']

    insert_query = """INSERT INTO class_decisions
                        (relation_id, user_id, approved)
                        VALUES (:relation_id, :user_id, :approved)"""
    result = db.engine.execute(insert_query, {
        'relation_id': relation_id,
        'user_id': user_id,
        'approved': decision
    })

def add_node_decision(user_id, name, onto_id, decision):
    relation_query = """SELECT id FROM nodes
                        WHERE onto_id = :onto_id
                            AND name = :name"""

    result = db.engine.execute(relation_query, {
        'onto_id': onto_id,
        'name': name,
    })

    node_id = result.fetchone()['id']

    result = db.engine.execute("""SELECT * FROM node_decisions 
            WHERE user_id = :user_id AND node_id = :node_id""", {'user_id': user_id, 'node_id': node_id})
    
    if result.fetchone():
        db.engine.execute("""UPDATE node_decisions SET approved = :decision
        WHERE user_id = :user_id AND node_id = :node_id""", 
        {'user_id': user_id, 'node_id': node_id, 'decision': approved})
    else:
        insert_query = """INSERT INTO node_decisions
                            (node_id, user_id, approved)
                            VALUES (:node_id, :user_id, :approved)"""
        result = db.engine.execute(insert_query, {
            'node_id': node_id,
            'user_id': user_id,
            'approved': decision
        })

# def get_decision(relation_id):
#     query = """SELECT * FROM class_decisions WHERE relation_id = :relation_id"""
#     result = db.engine.execute(query, {'relation_id': relation_id})
#     return accepted(result.fetchall())

def get_ontologies_on_server():
    ontologies = ['.'.join(f.split('.')[:-1]) for f in listdir("./data/owl/") if isfile(join("./data/owl/", f))]
    print(ontologies)
    return ontologies
