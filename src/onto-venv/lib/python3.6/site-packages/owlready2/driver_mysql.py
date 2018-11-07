# -*- coding: utf-8 -*-
# Owlready2
# Copyright (C) 2017-2018 Jean-Baptiste LAMY
# LIMICS (Laboratoire d'informatique médicale et d'ingénierie des connaissances en santé), UMR_S 1142
# University Paris 13, Sorbonne paris-Cité, Bobigny, France

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, os, os.path, turbodbc, time, re
from psycopg2.extras import execute_batch
from collections import defaultdict

import owlready2
from owlready2.base import *
from owlready2.driver import BaseMainGraph, BaseSubGraph
from owlready2.driver import _guess_format, _save
from owlready2.util import _int_base_62
from owlready2.base import _universal_abbrev_2_iri

class Graph(BaseMainGraph):
  _SUPPORT_CLONING = False
  def __init__(self, dbname = "owlready2_quadstore", new = False, clone = None, **kargs):
    #try:
    self.db = turbodbc.connect(dsn="MySQL", database = dbname, **kargs)
    
    self.sql      = self.db.cursor()
    self.execute  = self.sql.execute
    self.fetchone = self.sql.fetchone
    self.fetchall = self.sql.fetchall
    self.c_2_onto          = {}
    self.onto_2_subgraph   = {}
    self.last_numbered_iri = {}
    
    initialize_db = False
    try:
      self.execute("""SELECT * FROM quads LIMIT 1;""")
      self.fetchone()
      
    except:
      initialize_db = True
      self.db.rollback()
      
    if initialize_db:
      self.current_blank    = 0
      self.current_resource = 300 # 300 first values are reserved
      
      self.execute("""CREATE TABLE store (version INTEGER, current_blank INTEGER, current_resource INTEGER)""")
      self.execute("""INSERT INTO store VALUES (2, 0, 300)""")
      self.execute("""CREATE TABLE quads (c INTEGER, s VARCHAR(20) COLLATE utf8_bin, p VARCHAR(20) COLLATE utf8_bin, o TEXT COLLATE utf8_bin)""")
      self.execute("""CREATE TABLE ontologies (c INTEGER AUTO_INCREMENT PRIMARY KEY, iri TEXT, last_update DOUBLE)""")
      self.execute("""CREATE TABLE ontology_alias (iri TEXT, alias TEXT)""")
      self.execute("""CREATE TABLE resources (storid VARCHAR(20) COLLATE utf8_bin PRIMARY KEY, iri TEXT)""")
      self.sql.executemany("INSERT INTO resources VALUES (%s,%s)", _universal_abbrev_2_iri.items())
      self.execute("""CREATE INDEX index_resources_iri ON resources(iri(70))""")
      self.execute("""CREATE INDEX index_quads_s ON quads(s)""")
      self.execute("""CREATE INDEX index_quads_o ON quads(o(12))""")
      self.db.commit()
      
    else:
      if clone:
        s = "\n".join(clone.db.iterdump())
        self.db.cursor().executescript(s)
        
      self.execute("SELECT version, current_blank, current_resource FROM store")
      version, self.current_blank, self.current_resource = self.fetchone()
      
      
    self.execute("""PREPARE abbreviate1    FROM 'SELECT storid FROM resources WHERE iri=? LIMIT 1';""")
    self.execute("""PREPARE abbreviate2    FROM 'INSERT INTO resources VALUES (?,?)';""")
    self.execute("""PREPARE unabbreviate   FROM 'SELECT iri FROM resources WHERE storid=? LIMIT 1';""")
    self.execute("""PREPARE get_quads_sp   FROM 'SELECT o,c FROM quads WHERE s=? AND p=?';""")
    
    self.execute("""PREPARE get_triples_s  FROM 'SELECT p,o FROM quads WHERE s=?';""")
    self.execute("""PREPARE get_triples_sp FROM 'SELECT o FROM quads WHERE s=? AND p=?';""")
    self.execute("""PREPARE get_triples_po FROM 'SELECT s FROM quads WHERE p=? AND o=?';""")
    self.execute("""PREPARE get_triple_sp  FROM 'SELECT o FROM quads WHERE s=? AND p=? LIMIT 1';""")
    self.execute("""PREPARE get_triple_po  FROM 'SELECT s FROM quads WHERE p=? AND o=? LIMIT 1';""")
#    self.execute("""PREPARE get_transitive_sp FROM '
#WITH RECURSIVE transit(x)
#AS (      SELECT o FROM quads WHERE s=$1 AND p=$2
#UNION ALL SELECT quads.o FROM quads, transit WHERE quads.s=transit.x AND quads.p=$2)
#SELECT DISTINCT x FROM transit';""")
#    self.execute("""PREPARE get_transitive_po FROM '
#WITH RECURSIVE transit(x)
#AS (      SELECT s FROM quads WHERE p=$1 AND o=$2
#UNION ALL SELECT quads.s FROM quads, transit WHERE quads.p=$1 AND quads.o=transit.x)
#SELECT DISTINCT x FROM transit';""")

    self.execute("""PREPARE get_triples_sc  FROM 'SELECT p,o FROM quads WHERE c=? AND s=?';""")
    self.execute("""PREPARE get_triples_spc FROM 'SELECT o FROM quads WHERE c=? AND s=? AND p=?';""")
    self.execute("""PREPARE get_triples_poc FROM 'SELECT s FROM quads WHERE c=? AND p=? AND o=?';""")
    self.execute("""PREPARE get_triple_spc  FROM 'SELECT o FROM quads WHERE c=? AND s=? AND p=? LIMIT 1';""")
    self.execute("""PREPARE get_triple_poc  FROM 'SELECT s FROM quads WHERE c=? AND p=? AND o=? LIMIT 1';""")
#    self.execute("""PREPARE get_transitive_spc FROM '
#WITH RECURSIVE transit(x)
#AS (      SELECT o FROM quads WHERE s=$1 AND p=$2 AND c=$3
#UNION ALL SELECT quads.o FROM quads, transit WHERE quads.s=transit.x AND quads.p=$2 AND quads.c=$3)
#SELECT DISTINCT x FROM transit';""")
#    self.execute("""PREPARE get_transitive_poc FROM '
#WITH RECURSIVE transit(x)
#AS (      SELECT s FROM quads WHERE p=$1 AND o=$2 AND c=$3
#UNION ALL SELECT quads.s FROM quads, transit WHERE quads.p=$1 AND quads.o=transit.x AND quads.c=$3)
#SELECT DISTINCT x FROM transit';""")


   
  def sub_graph(self, onto):
    new_in_quadstore = False
    self.execute("SELECT c FROM ontologies WHERE iri=?", (onto.base_iri,))
    c = self.fetchone()
    if c is None:
      self.execute("SELECT ontologies.c FROM ontologies, ontology_alias WHERE ontology_alias.alias=? AND ontologies.iri=ontology_alias.iri", (onto.base_iri,))
      c = self.fetchone()
      if c is None:
        new_in_quadstore = True
        self.execute("INSERT INTO ontologies (iri, last_update) VALUES (?, 0)", (onto.base_iri,))
        self.execute("SELECT c FROM ontologies WHERE iri=?", (onto.base_iri,))
        c = self.fetchone()
    c = c[0]
    self.c_2_onto[c] = onto
    
    return SubGraph(self, onto, c, self.db, self.sql), new_in_quadstore
  
  def ontologies_iris(self):
    self.execute("SELECT iri FROM ontologies")
    for (iri,) in self.fetchall(): yield iri
   
  def get_storid_dict(self):
    self.execute("SELECT storid, iri FROM resources")
    return dict(self.fetchall())
     
  def abbreviate(self, iri):
    self.execute("SELECT storid FROM resources WHERE iri=? LIMIT 1", (iri,))
    #self.execute("EXECUTE abbreviate1 USING %s", (iri,))
    r = self.fetchone()
    if r: return r[0]
    self.current_resource += 1
    storid = _int_base_62(self.current_resource)
    self.execute("INSERT INTO resources VALUES (?,?)", (storid, iri))
    #self.execute("EXECUTE abbreviate2 USING %s,%s", (storid, iri))
    return storid
  
  def unabbreviate(self, storid):
    self.execute("SELECT iri FROM resources WHERE storid=? LIMIT 1", (storid,))
    #self.execute("EXECUTE unabbreviate USING %s", (storid,))
    return self.fetchone()[0]
  
  def new_numbered_iri(self, prefix):
    if prefix in self.last_numbered_iri:
      i = self.last_numbered_iri[prefix] = self.last_numbered_iri[prefix] + 1
      return "%s%s" % (prefix, i)
    else:
      self.execute("SELECT iri FROM resources WHERE iri GLOB ? ORDER BY LENGTH(iri) DESC, iri DESC", ("%s*" % prefix,))
      while True:
        iri = self.fetchone()
        if not iri: break
        num = iri[0][len(prefix):]
        if num.isdigit():
          self.last_numbered_iri[prefix] = i = int(num) + 1
          return "%s%s" % (prefix, i)
        
    self.last_numbered_iri[prefix] = 1
    return "%s1" % prefix
  
  def refactor(self, storid, new_iri):
    self.execute("UPDATE resources SET iri=? WHERE storid=?", (new_iri, storid,))
    
    
    
  def commit(self):
    self.execute("UPDATE store SET current_blank=?, current_resource=?", (self.current_blank, self.current_resource))
    self.db.commit()
    
    
    
  def context_2_user_context(self, c): return self.c_2_onto[c]

  def new_blank_node(self):
    self.current_blank += 1
    return "_%s" % _int_base_62(self.current_blank)
  
  def get_triples(self, s, p, o):
    if s is None:
      if p is None:
        if o is None: self.execute("SELECT s,p,o FROM quads")
        else:         self.execute("SELECT s,p,o FROM quads WHERE o=?", (o,))
      else:
        if o is None: self.execute("SELECT s,p,o FROM quads WHERE p=?", (p,))
        else:         self.execute("SELECT s,p,o FROM quads WHERE p=? AND o=?", (p, o,))
    else:
      if p is None:
        if o is None: self.execute("SELECT s,p,o FROM quads WHERE s=?", (s,))
        else:         self.execute("SELECT s,p,o FROM quads WHERE s=? AND o=?", (s, o,))
      else:
        if o is None: self.execute("SELECT s,p,o FROM quads WHERE s=? AND p=?", (s, p,))
        else:         self.execute("SELECT s,p,o FROM quads WHERE s=? AND p=? AND o=?", (s, p, o,))
    return self.fetchall()
    
  def get_quads(self, s, p, o, c):
    if c is None:
      if s is None:
        if p is None:
          if o is None: self.execute("SELECT s,p,o,c FROM quads")
          else:         self.execute("SELECT s,p,o,c FROM quads WHERE o=?", (o,))
        else:
          if o is None: self.execute("SELECT s,p,o,c FROM quads WHERE p=?", (p,))
          else:         self.execute("SELECT s,p,o,c FROM quads WHERE p=? AND o=?", (p, o,))
      else:
        if p is None:
          if o is None: self.execute("SELECT s,p,o,c FROM quads WHERE s=?", (s,))
          else:         self.execute("SELECT s,p,o,c FROM quads WHERE s=? AND o=?", (s, o,))
        else:
          if o is None: self.execute("SELECT s,p,o,c FROM quads WHERE s=? AND p=?", (s, p,))
          else:         self.execute("SELECT s,p,o,c FROM quads WHERE s=? AND p=? AND o=?", (s, p, o,))
    else:
      if s is None:
        if p is None:
          if o is None: self.execute("SELECT s,p,o,c FROM quads WHERE c=?", (c,))
          else:         self.execute("SELECT s,p,o,c FROM quads WHERE c=? AND o=?", (c, o,))
        else:
          if o is None: self.execute("SELECT s,p,o,c FROM quads WHERE c=? AND p=?", (c, p,))
          else:         self.execute("SELECT s,p,o,c FROM quads WHERE c=? AND p=? AND o=?", (c, p, o,))
      else:
        if p is None:
          if o is None: self.execute("SELECT s,p,o,c FROM quads WHERE c=? AND s=?", (c, s,))
          else:         self.execute("SELECT s,p,o,c FROM quads WHERE c=? AND s=? AND o=?", (c, s, o,))
        else:
          if o is None: self.execute("SELECT s,p,o,c FROM quads WHERE c=? AND s=? AND p=?", (c, s, p,))
          else:         self.execute("SELECT s,p,o,c FROM quads WHERE c=? AND s=? AND p=? AND o=?", (c, s, p, o,))
    return self.fetchall()
  
  def get_quads_sp(self, s, p):
    self.execute("SELECT o,c FROM quads WHERE s=? AND p=?", (s, p))
    #self.execute("EXECUTE get_quads_sp USING ?,?", (s, p))
    return self.fetchall()
  
  def get_pred(self, s):
    self.execute("SELECT DISTINCT p FROM quads WHERE s=?", (s,))
    for (x,) in self.fetchall(): yield x
    
  def get_triples_s(self, s):
    self.execute("SELECT p,o FROM quads WHERE s=?", (s,))
    #self.execute("EXECUTE get_triples_s USING ?", (s))
    return self.fetchall()
  
  def get_triples_sp(self, s, p):
    self.execute("SELECT o FROM quads WHERE s=? AND p=?", (s, p))
    #self.execute("EXECUTE get_triples_sp USING ?,?", (s, p))
    for (x,) in self.fetchall(): yield x
    
  def get_triples_po(self, p, o):
    self.execute("SELECT s FROM quads WHERE p=? AND o=?", (p, o))
    #self.execute("EXECUTE get_triples_po USING ?,?", (p, o))
    for (x,) in self.fetchall(): yield x
    
  def get_triple_sp(self, s = None, p = None):
    self.execute("SELECT o FROM quads WHERE s=? AND p=? LIMIT 1", (s, p))
    #self.execute("EXECUTE get_triple_sp USING ?,?", (s, p))
    r = self.fetchone()
    if r: return r[0]
    return None
  
  def get_triple_po(self, p = None, o = None):
    self.execute("SELECT s FROM quads WHERE p=? AND o=? LIMIT 1", (p, o))
    #self.execute("EXECUTE get_triple_po USING ?,?", (p, o))
    r = self.fetchone()
    if r: return r[0]
    return None
  
  def has_triple(self, s = None, p = None, o = None):
    if s is None:
      if p is None:
        if o is None: self.execute("SELECT s FROM quads LIMIT 1")
        else:         self.execute("SELECT s FROM quads WHERE o=? LIMIT 1", (o,))
      else:
        if o is None: self.execute("SELECT s FROM quads WHERE p=? LIMIT 1", (p,))
        else:         self.execute("SELECT s FROM quads WHERE p=? AND o=? LIMIT 1", (p, o))
    else:
      if p is None:
        if o is None: self.execute("SELECT s FROM quads WHERE s=? LIMIT 1", (s,))
        else:         self.execute("SELECT s FROM quads WHERE s=? AND o=? LIMIT 1", (s, o))
      else:
        if o is None: self.execute("SELECT s FROM quads WHERE s=? AND p=? LIMIT 1", (s, p))
        else:         self.execute("SELECT s FROM quads WHERE s=? AND p=? AND o=? LIMIT 1", (s, p, o))
    return not self.fetchone() is None
  
  def _del_triple(self, s, p, o):
    if s is None:
      if p is None:
        if o is None: self.execute("DELETE FROM quads")
        else:         self.execute("DELETE FROM quads WHERE o=?", (o,))
      else:
        if o is None: self.execute("DELETE FROM quads WHERE p=?", (p,))
        else:         self.execute("DELETE FROM quads WHERE p=? AND o=?", (p, o,))
    else:
      if p is None:
        if o is None: self.execute("DELETE FROM quads WHERE s=?", (s,))
        else:         self.execute("DELETE FROM quads WHERE s=? AND o=?", (s, o,))
      else:
        if o is None: self.execute("DELETE FROM quads WHERE s=? AND p=?", (s, p,))
        else:         self.execute("DELETE FROM quads WHERE s=? AND p=? AND o=?", (s, p, o,))
        
  def search(self, prop_vals, c = None):
    tables     = []
    conditions = []
    params     = []
    excepts    = []
    i = 0
    
    for k, v in prop_vals:
      if v is None:
        excepts.append(k)
        continue
      
      i += 1
      tables.append("quads q%s" % i)
      if not c is None:
        conditions  .append("q%s.c = ?" % i)
        params      .append(c)
        
      if   k == "iri":
        if i > 1: conditions.append("q%s.s = q1.s" % i)
        tables    .append("resources")
        conditions.append("resources.storid = q%s.s" % i)
        if "*" in v: conditions.append("resources.iri GLOB %s")
        else:        conditions.append("resources.iri = %s")
        params.append(v)
        
      elif k == "is_a":
        if i > 1: conditions.append("q%s.s = q1.s" % i)
        conditions.append("(q%s.p = '%s' OR q%s.p = '%s') AND q%s.o IN (%s)" % (i, rdf_type, i, rdfs_subclassof, i, ",".join("%s" for i in v)))
        params    .extend(v)
        
      elif k == "type":
        if i > 1: conditions.append("q%s.s = q1.s" % i)
        conditions.append("q%s.p = '%s' AND q%s.o IN (%s)" % (i, rdf_type, i, ",".join("%s" for i in v)))
        params    .extend(v)
        
      elif k == "subclass_of":
        if i > 1: conditions.append("q%s.s = q1.s" % i)
        conditions.append("q%s.p = '%s' AND q%s.o IN (%s)" % (i, rdfs_subclassof, i, ",".join("%s" for i in v)))
        params    .extend(v)
        
      elif isinstance(k, tuple): # Prop with inverse
        if i == 1: # Does not work if it is the FIRST => add a dumb first.
          i += 1
          tables.append("quads q%s" % i)
          if not c is None:
            conditions  .append("q%s.c = ?" % i)
            params      .append(c)
            
        if v.startswith('"*"'):
          cond1 = "q%s.s = q1.s AND q%s.p = ?" % (i, i)
          cond2 = "q%s.o = q1.s AND q%s.p = ?" % (i, i)
          params.extend([k[0], k[1]])
        else:
          cond1 = "q%s.s = q1.s AND q%s.p = ? AND q%s.o = ?" % (i, i, i)
          cond2 = "q%s.o = q1.s AND q%s.p = ? AND q%s.s = ?" % (i, i, i)
          params.extend([k[0], v, k[1], v])
        conditions  .append("((%s) OR (%s))" % (cond1, cond2))
        
      else: # Prop without inverse
        if i > 1: conditions.append("q%s.s = q1.s" % i)
        conditions.append("q%s.p = ?" % i)
        params    .append(k)
        if "*" in v:
          if   v.startswith('"*"'):
            conditions.append("q%s.o GLOB '*'" % i)
          else:
            conditions.append("q%s.o GLOB ?" % i)
            params    .append(v)
        else:
          conditions.append("q%s.o = ?" % i)
          params    .append(v)
          
    req = "SELECT DISTINCT q1.s from %s WHERE %s" % (", ".join(tables), " AND ".join(conditions))
    
    if excepts:
      conditions = []
      for except_p in excepts:
        if isinstance(except_p, tuple): # Prop with inverse
          conditions.append("quads.s = candidates.s AND quads.p = %s")
          params    .append(except_p[0])
          conditions.append("quads.o = candidates.s AND quads.p = %s")
          params    .append(except_p[1])
        else: # No inverse
          conditions.append("quads.s = candidates.s AND quads.p = %s")
          params    .append(except_p)
          
          
      req = """
WITH candidates(s) AS (%s)
SELECT s FROM candidates
EXCEPT SELECT candidates.s FROM candidates, quads WHERE (%s)""" % (req, ") OR (".join(conditions))
      
    #print(prop_vals)
    #print(req)
    #print(params)
    
    self.execute(req, params)
    return self.fetchall()
  
  def _punned_entities(self):
    from owlready2.base import rdf_type, owl_class, owl_named_individual
    self.execute("SELECT q1.s FROM quads q1, quads q2 WHERE q1.s=q2.s AND q1.p=? AND q2.p=? AND q1.o=? AND q2.o=?", (rdf_type, rdf_type, owl_class, owl_named_individual))
    return [storid for (storid,) in self.fetchall()]
  
    
  def __len__(self):
    self.execute("SELECT COUNT(*) FROM quads")
    return self.fetchone()[0]

  
  # Reimplemented using RECURSIVE SQL structure, for performance
  def __get_transitive_sp(self, s, p):
#    for (x,) in self.execute("""
#WITH RECURSIVE transit(x)
#AS (      SELECT o FROM quads WHERE s=? AND p=?
#UNION ALL SELECT quads.o FROM quads, transit WHERE quads.s=transit.x AND quads.p=?)
#SELECT DISTINCT x FROM transit""", (s, p, p)).fetchall(): yield x
    self.execute("EXECUTE get_transitive_sp USING ?,?", (s, p))
    for (x,) in self.fetchall(): yield x
    
  # Reimplemented using RECURSIVE SQL structure, for performance
  def __get_transitive_po(self, p, o):
    self.execute("EXECUTE get_transitive_po USING ?,?", (p, o))
    for (x,) in self.fetchall(): yield x

# Slower than Python implementation
#   def get_transitive_sym2(self, s, p):
#     r = { s }
#     self.execute("""
# WITH RECURSIVE transit(s,o)
# AS (  SELECT s,o from quads WHERE (s=? OR o=?) AND (p=?)
# UNION SELECT quads.s,quads.o FROM quads, transit WHERE (quads.s=transit.s OR quads.o=transit.o OR quads.s=transit.o OR quads.o=transit.s) AND quads.p=?)
# SELECT s, o FROM transit""", (s, s, p, p))
#     for (s, o) in self.fetchall():
#       r.add(s)
#       r.add(o)
#     yield from r
    

  def _destroy_collect_storids(self, destroyed_storids, modified_relations, storid):
    for (blank_using,) in list(self.execute("""SELECT s FROM quads WHERE o=? AND p IN (
    '?', '?', '?', '?', '?', '?', '?', '?', '?', '?', '?') AND substr(s, 1, 1)='_'""" % (
      SOME,
      ONLY,
      VALUE,
      owl_onclass,
      owl_onproperty,
      owl_complementof,
      owl_inverse_property,
      owl_ondatarange,
      owl_annotatedsource,
      owl_annotatedproperty,
      owl_annotatedtarget,
    ), (storid,))):
      if not blank_using in destroyed_storids:
        destroyed_storids.add(blank_using)
        self._destroy_collect_storids(destroyed_storids, modified_relations, blank_using)
        
    for (c, blank_using) in list(self.execute("""SELECT c, s FROM quads WHERE o=? AND p=? AND substr(s, 1, 1)='_'""" % (
      rdf_first,
    ), (storid,))):
      list_user, root, previouss, nexts, length = self._rdf_list_analyze(blank_using)
      destroyed_storids.update(previouss)
      destroyed_storids.add   (blank_using)
      destroyed_storids.update(nexts)
      if not list_user in destroyed_storids:
        destroyed_storids.add(list_user)
        self._destroy_collect_storids(destroyed_storids, modified_relations, list_user)
        
  def _rdf_list_analyze(self, blank):
    previouss = []
    nexts     = []
    length    = 1
    #b         = next_ = self.get_triple_sp(blank, rdf_rest)
    b         = self.get_triple_sp(blank, rdf_rest)
    while b != rdf_nil:
      nexts.append(b)
      length += 1
      b       = self.get_triple_sp(b, rdf_rest)
      
    b         = self.get_triple_po(rdf_rest, blank)
    if b:
      while b:
        previouss.append(b)
        length += 1
        root    = b
        b       = self.get_triple_po(rdf_rest, b)
    else:
      root = blank
      
    self.execute("SELECT s FROM quads WHERE o=? LIMIT 1", (root,))
    list_user = self.fetchone()
    if list_user: list_user = list_user[0]
    return list_user, root, previouss, nexts, length
  
  def destroy_entity(self, storid, destroyer, relation_updater):
    destroyed_storids   = { storid }
    modified_relations  = defaultdict(set)
    self._destroy_collect_storids(destroyed_storids, modified_relations, storid)
    
    for s,p in self.execute("SELECT DISTINCT s,p FROM quads WHERE o IN (%s)" % ",".join(["?" for i in destroyed_storids]), tuple(destroyed_storids)):
      if not s in destroyed_storids:
        modified_relations[s].add(p)
        
    # Two separate loops because high level destruction must be ended before removing from the quadstore (high level may need the quadstore)
    for storid in destroyed_storids:
      destroyer(storid)
      
    for storid in destroyed_storids:
      #self.execute("SELECT s,p,o FROM quads WHERE s=? OR o=?", (self.c, storid, storid))
      self.execute("DELETE FROM quads WHERE s=? OR o=?", (storid, storid))
      
    for s, ps in modified_relations.items():
      relation_updater(destroyed_storids, s, ps)
      
    return destroyed_storids
  
  def _iter_ontology_iri(self, c = None):
    if c:
      self.execute("SELECT iri FROM ontologies WHERE c=?", (c,))
      return self.fetchone()[0]
    else:
      self.execute("SELECT c, iri FROM ontologies")
      return self.fetchall()
    
  def _iter_triples(self, quads = False, sort_by_s = False):
    cursor = self.db.cursor() # Use a new cursor => can iterate without laoding all data in a big list, while still being able to query the default cursor
    if quads:
      if sort_by_s: cursor.execute("SELECT c,s,p,o FROM quads ORDER BY s")
      else:         cursor.execute("SELECT c,s,p,o FROM quads")
    else:
      if sort_by_s: cursor.execute("SELECT s,p,o FROM quads ORDER BY s")
      else:         cursor.execute("SELECT s,p,o FROM quads")
    return cursor
  
        
  
class SubGraph(BaseSubGraph):
  def __init__(self, parent, onto, c, db, sql):
    BaseSubGraph.__init__(self, parent, onto)
    self.c      = c
    self.db     = db
    self.sql    = sql
    self.execute  = self.sql.execute
    self.fetchone = self.sql.fetchone
    self.fetchall = self.sql.fetchall
    self.abbreviate       = parent.abbreviate
    self.unabbreviate     = parent.unabbreviate
    self.new_numbered_iri = parent.new_numbered_iri
    
    self.parent.onto_2_subgraph[onto] = self
    
  def create_parse_func(self, filename = None, delete_existing_triples = True, datatype_attr = "http://www.w3.org/1999/02/22-rdf-syntax-ns#datatype"):
    values       = []
    abbrevs      = {}
    new_abbrevs  = []
    def abbreviate(iri): # Re-implement for speed
      storid = abbrevs.get(iri)
      if not storid is None: return storid
      self.execute("SELECT storid FROM resources WHERE iri=? LIMIT 1", (iri,))
      #self.execute("EXECUTE abbreviate1 USING ?", (iri,))
      r = self.fetchone()
      if r:
        abbrevs[iri] = r[0]
        return r[0]
      self.parent.current_resource += 1
      storid = _int_base_62(self.parent.current_resource)
      new_abbrevs.append((storid, iri))
      abbrevs[iri] = storid
      return storid
    
    def on_prepare_triple(s, p, o):
      if not s.startswith("_"): s = abbreviate(s)
      p = abbreviate(p)
      if not (o.startswith("_") or o.startswith('"')): o = abbreviate(o)
      
      values.append((s,p,o))
      
    def new_literal(value, attrs):
      lang = attrs.get("http://www.w3.org/XML/1998/namespacelang")
      if lang: return '"%s"@%s' % (value, lang)
      datatype = attrs.get(datatype_attr)
      if datatype: return '"%s"%s' % (value, abbreviate(datatype))
      return '"%s"' % (value)
    
    def on_finish():
      if filename: date = os.path.getmtime(filename)
      else:        date = time.time()
      
      if delete_existing_triples: self.execute("DELETE FROM quads WHERE c=?", (self.c,))
      
      if len(self.parent) < 100000:
        self.execute("""DROP INDEX index_resources_iri ON resources""")
        self.execute("""DROP INDEX index_quads_s ON quads""")
        self.execute("""DROP INDEX index_quads_o ON quads""")
        reindex = True
      else:
        reindex = False
        
      if owlready2.namespace._LOG_LEVEL: print("* OwlReady2 * Importing %s triples from ontology %s ..." % (len(values), self.onto.base_iri), file = sys.stderr)
      
      t = time.time()
      #self.sql.execute("PREPARE stmt AS INSERT INTO resources VALUES ($1,$2)")
      #execute_batch(self.sql, "EXECUTE stmt (?,?)", new_abbrevs)
      #self.sql.execute("DEALLOCATE stmt")
      self.sql.executemany("INSERT INTO resources VALUES (?,?)", new_abbrevs)
      
      #self.sql.execute("PREPARE stmt AS INSERT INTO quads VALUES (?,$1,$2,$3)" % self.c)
      #execute_batch(self.sql, "EXECUTE stmt (?,?,?)", values)
      #self.sql.execute("DEALLOCATE stmt")
      self.sql.executemany("INSERT INTO quads VALUES (%s,?,?,?)" % self.c, values)
      
      print(time.time() - t, file = sys.stderr)
      
      if reindex:
        self.execute("""CREATE INDEX index_resources_iri ON resources(iri(70))""")
        self.execute("""CREATE INDEX index_quads_s ON quads(s)""")
        self.execute("""CREATE INDEX index_quads_o ON quads(o(12))""")
        
        
      self.execute("SELECT resources.iri FROM quads, resources WHERE quads.c=? AND quads.o=? AND resources.storid=quads.s LIMIT 1", (self.c, owl_ontology))
      onto_base_iri = self.fetchone()
      
      if onto_base_iri:
        onto_base_iri = onto_base_iri[0]
        self.execute("SELECT resources.iri FROM quads, resources WHERE quads.c=? AND resources.storid=quads.s AND resources.iri LIKE ? LIMIT 1", (self.c, onto_base_iri + "#%"))
        use_hash = self.fetchone()
        if use_hash: onto_base_iri = onto_base_iri + "#"
        else:
          self.execute("SELECT resources.iri FROM quads, resources WHERE quads.c=? AND resources.storid=quads.s AND resources.iri LIKE ? LIMIT 1", (self.c, onto_base_iri + "/%"))
          use_slash = self.fetchone()
          if use_slash: onto_base_iri = onto_base_iri + "/"
          else:         onto_base_iri = onto_base_iri + "#"
        self.execute("UPDATE ontologies SET last_update=?,iri=? WHERE c=?", (date, onto_base_iri, self.c,))
      else:
        self.execute("UPDATE ontologies SET last_update=? WHERE c=?", (date, self.c,))
        
      return onto_base_iri
      
    return on_prepare_triple, self.parent.new_blank_node, new_literal, abbreviate, on_finish


  def context_2_user_context(self, c): return self.parent.c_2_onto[c]
 
  def add_ontology_alias(self, iri, alias):
    self.execute("INSERT into ontology_alias VALUES (?,?)", (iri, alias))
    
  def get_last_update_time(self):
    self.execute("SELECT last_update FROM ontologies WHERE c=?", (self.c,))
    return self.fetchone()[0]
  
  def destroy(self):
    self.execute("DELETE FROM quads WHERE c=?",      (self.c,))
    self.execute("DELETE FROM ontologies WHERE c=?", (self.c,))
    
  def _set_triple(self, s, p, o):
    if (s is None) or (p is None) or (o is None): raise ValueError
    self.execute("DELETE FROM quads WHERE c=? AND s=? AND p=?", (self.c, s, p,))
    self.execute("INSERT INTO quads VALUES (?, ?, ?, ?)", (self.c, s, p, o))
    
  def _add_triple(self, s, p, o):
    if (s is None) or (p is None) or (o is None): raise ValueError
    self.execute("INSERT INTO quads VALUES (?, ?, ?, ?)", (self.c, s, p, o))
    
  def _del_triple(self, s, p, o):
    if s is None:
      if p is None:
        if o is None: self.execute("DELETE FROM quads WHERE c=?", (self.c,))
        else:         self.execute("DELETE FROM quads WHERE c=? AND o=?", (self.c, o,))
      else:
        if o is None: self.execute("DELETE FROM quads WHERE c=? AND p=?", (self.c, p,))
        else:         self.execute("DELETE FROM quads WHERE c=? AND p=? AND o=?", (self.c, p, o,))
    else:
      if p is None:
        if o is None: self.execute("DELETE FROM quads WHERE c=? AND s=?", (self.c, s,))
        else:         self.execute("DELETE FROM quads WHERE c=? AND s=? AND o=?", (self.c, s, o,))
      else:
        if o is None: self.execute("DELETE FROM quads WHERE c=? AND s=? AND p=?", (self.c, s, p,))
        else:         self.execute("DELETE FROM quads WHERE c=? AND s=? AND p=? AND o=?", (self.c, s, p, o,))
        
  def get_triples(self, s, p, o):
    if s is None:
      if p is None:
        if o is None: self.execute("SELECT s,p,o FROM quads WHERE c=?", (self.c,))
        else:         self.execute("SELECT s,p,o FROM quads WHERE c=? AND o=?", (self.c, o,))
      else:
        if o is None: self.execute("SELECT s,p,o FROM quads WHERE c=? AND p=?", (self.c, p,))
        else:         self.execute("SELECT s,p,o FROM quads WHERE c=? AND p=? AND o=?", (self.c, p, o,))
    else:
      if p is None:
        if o is None: self.execute("SELECT s,p,o FROM quads WHERE c=? AND s=?", (self.c, s,))
        else:         self.execute("SELECT s,p,o FROM quads WHERE c=? AND s=? AND o=?", (self.c, s, o,))
      else:
        if o is None: self.execute("SELECT s,p,o FROM quads WHERE c=? AND s=? AND p=?", (self.c, s, p,))
        else:         self.execute("SELECT s,p,o FROM quads WHERE c=? AND s=? AND p=? AND o=?", (self.c, s, p, o,))
    return self.fetchall()
  
  def get_triples_s(self, s):
    self.execute("SELECT p,o FROM quads WHERE c=? AND s=?", (self.c, s,))
    #self.execute("EXECUTE get_triples_sc USING ?,?", (self.c, s,))
    return self.fetchall()
  
  def get_triples_sp(self, s, p):
    self.execute("SELECT o FROM quads WHERE c=? AND s=? AND p=?", (self.c, s, p,))
    #self.execute("EXECUTE get_triples_spc USING ?,?,?", (self.c, s, p))
    for (x,) in self.fetchall(): yield x
    
  def get_triples_po(self, p, o):
    self.execute("SELECT s FROM quads WHERE c=? AND p=? AND o=?", (self.c, p, o,))
    #self.execute("EXECUTE get_triples_poc USING ?,?,?", (self.c, p, o))
    for (x,) in self.fetchall(): yield x
    
  def get_triple_sp(self, s, p):
    self.execute("SELECT o FROM quads WHERE c=? AND s=? AND p=? LIMIT 1", (self.c, s, p,))
    #self.execute("EXECUTE get_triple_spc USING ?,?,?", (self.c, s, p))
    r = self.fetchone()
    if r: return r[0]
    return None
  
  def get_triple_po(self, p, o):
    self.execute("SELECT s FROM quads WHERE c=? AND p=? AND o=? LIMIT 1", (self.c, p, o,))
    #self.execute("EXECUTE get_triple_poc USING ?,?,?", (self.c, p, o))
    r = self.fetchone()
    if r: return r[0]
    return None
  
  def get_pred(self, s):
    self.execute("SELECT DISTINCT p FROM quads WHERE c=? AND s=?", (self.c, s,))
    for (x,) in self.fetchall(): yield x
    
  def has_triple(self, s = None, p = None, o = None):
    if s is None:
      if p is None:
        if o is None: self.execute("SELECT s FROM quads WHERE c=? LIMIT 1", (self.c,))
        else:         self.execute("SELECT s FROM quads WHERE c=? AND o=? LIMIT 1", (self.c, o,))
      else:
        if o is None: self.execute("SELECT s FROM quads WHERE c=? AND p=? LIMIT 1", (self.c, p,))
        else:         self.execute("SELECT s FROM quads WHERE c=? AND p=? AND o=? LIMIT 1", (self.c, p, o,))
    else:
      if p is None:
        if o is None: self.execute("SELECT s FROM quads WHERE c=? AND s=? LIMIT 1", (self.c, s,))
        else:         self.execute("SELECT s FROM quads WHERE c=? AND s=? AND o=? LIMIT 1", (self.c, s, o,))
      else:
        if o is None: self.execute("SELECT s FROM quads WHERE c=? AND s=? AND p=? LIMIT 1", (self.c, s, p,))
        else:         self.execute("SELECT s FROM quads WHERE c=? AND s=? AND p=? AND o=? LIMIT 1", (self.c, s, p, o,))
    return not self.fetchone() is None
  
  def get_quads(self, s, p, o, c):
    return [(s, p, o, self.c) for (s, p, o) in self.get_triples(s, p, o)]
  
  def search(self, prop_vals, c = None): return self.parent.search(prop_vals, self.c)
  
  def __len__(self):
    self.execute("SELECT COUNT(*) FROM quads WHERE c=?", (self.c,))
    return self.fetchone()[0]


  def _iter_ontology_iri(self, c = None):
    if c:
      self.execute("SELECT iri FROM ontologies WHERE c=?", (c,))
      return self.fetchone()[0]
    else:
      self.execute("SELECT c, iri FROM ontologies")
      return self.fetchall()
    
  def _iter_triples(self, quads = False, sort_by_s = False):
    cursor = self.db.cursor() # Use a new cursor => can iterate without laoding all data in a big list, while still being able to query the default cursor
    if quads:
      if sort_by_s: cursor.execute("SELECT c,s,p,o FROM quads WHERE c=? ORDER BY s", (self.c,))
      else:         cursor.execute("SELECT c,s,p,o FROM quads WHERE c=?", (self.c,))
    else:
      if sort_by_s: cursor.execute("SELECT s,p,o FROM quads WHERE c=? ORDER BY s", (self.c,))
      else:         cursor.execute("SELECT s,p,o FROM quads WHERE c=?", (self.c,))
    return cursor

  
  
  # Reimplemented using RECURSIVE SQL structure, for performance
  def __get_transitive_sp(self, s, p):
    self.execute("EXECUTE get_transitive_spc USING ?,?", (s, p, c))
    for (x,) in self.fetchall(): yield x
    
  # Reimplemented using RECURSIVE SQL structure, for performance
  def __get_transitive_po(self, p, o):
    self.execute("EXECUTE get_transitive_poc USING ?,?", (p, o, c))
    for (x,) in self.fetchall(): yield x

#  def get_transitive_sym(self, s, p):
#    r = { s }
#    for (s, o) in self.execute("""
#WITH RECURSIVE transit(s,o)
#AS (  SELECT s,o from quads WHERE (s=? OR o=?) AND p=? AND c=?
#    UNION SELECT quads.s,quads.o FROM quads, transit WHERE (quads.s=transit.s OR quads.o=transit.o OR quads.s=transit.o OR quads.o=transit.s) AND quads.p=? AND quads.c=?)
#SELECT s, o FROM transit""", (s, s, p, self.c, p, self.c)):
#      r.add(s)
#      r.add(o)
#    yield from r
