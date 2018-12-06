import sqlite3
import subprocess
import sys
import os
from shutil import copyfile
from rdflib.namespace import RDFS

RESTRICTIONS = "Restriction_removal-1.0-SNAPSHOT-jar-with-dependencies.jar"
CLASSES = "Class_removal-1.0-SNAPSHOT-jar-with-dependencies.jar"
SUBCLASSES = "Subclass_removal-1.0-SNAPSHOT-jar-with-dependencies.jar"

def accepted(decisions):
    count_accept = 0
    count_reject = 0
    for d in decisions:
        if d == 0:
            count_reject += 1
        else:
            count_accept += 1
    return bool(count_accept >= count_reject)

def generate_final_ontology(name):
    conn = sqlite3.connect('onto.db')
    c = conn.cursor()
    # print("""SELECT id FROM ontologies WHERE name = '""" + name.strip() + "'")
    result = c.execute("""SELECT * FROM ontologies""")
    onto_id = None
    for row in result.fetchall():
        if row[1] == name:
            onto_id = row[0]
            break
    owl_path = './data/final/' + name + '.owl'
    if not os.path.isfile(owl_path):
        try:
            copyfile('./data/owl/' + name + '.owl', owl_path)
        except:
            raise RuntimeError

    result = c.execute("""SELECT * FROM class_relations WHERE onto_id = ?""", (onto_id,))
    relations = result.fetchall()
    for r in relations:
        result = c.execute("""SELECT * FROM class_decisions WHERE relation_id = ?""", (r[0],))
        decisions = result.fetchall()
        if decisions:
            if not accepted([d[2] for d in decisions]):
                if r[4] == str(RDFS.subClassOf):
                    print("subclass")
                    try:
                        subprocess.run(['java', '-jar', SUBCLASSES, r[2], r[3], owl_path])
                    except:
                        raise RuntimeError
                else:
                    print("restriction")
                    try:
                        subprocess.run(['java', '-jar', RESTRICTIONS, r[2], r[1], r[3], owl_path])
                    except:
                        raise RuntimeError
            c.execute("""DELETE FROM class_relations WHERE id = ?""", (r[0],))
    
    result = c.execute("""SELECT * FROM nodes WHERE onto_id = ?""", (onto_id,))
    nodes = result.fetchall()
    for n in nodes:
        result = c.execute("""SELECT * FROM node_decisions WHERE node_id = ?""", (n[0],))
        decisions = result.fetchall()
        if decisions:
            if not accepted([d[2] for d in decisions]):
                print("class")
                try:
                    subprocess.run(['java', '-jar', CLASSES, n[2], owl_path])
                except:
                    raise RuntimeError
            c.execute("""DELETE FROM nodes WHERE id = ?""", (n[0],))
    
    conn.commit()
    conn.close()
    
    