# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

import webapp2, cgi, re
import urllib
from encodingUtils import fix_encoding

SOLVER_NAME = "תשבצל'ה"

class Answer:
	def __init__(self, answer, definition, source, total_stars, raters_count):
		self.answer = answer
		self.definition = definition
		self.source = source
		self.total_stars = total_stars
		self.raters_count = raters_count

	def __hash__(self):
		return hash((self.answer, self.definition))

	def __eq__(self, other):
		return (self.answer, self.definition) == (other.answer, other.definition)

class NDBAnswer(ndb.Model):
    # """Models an individual answer entry with ranking and source"""
    answer = ndb.StringProperty()
    definition = ndb.StringProperty()
    source = ndb.StringProperty()
    total_stars = ndb.IntegerProperty()
    raters_count = ndb.IntegerProperty()

    @classmethod
    def query_answer(cls, new_definition):
    	# """returns the query in which definition is as given"""
    	return cls.query(cls.definition == urllib.quote(new_definition.encode('utf'))).order(-cls.total_stars * 1.0 / cls.raters_count)

def NDBAnswer_to_Answer(ndb_answer):
	return Answer(urllib.unquote(str(ndb_answer.answer)), \
				  urllib.unquote(str(ndb_answer.definition)), \
				  urllib.unquote(str(ndb_answer.source)), \
				  ndb_answer.total_stars, \
                  ndb_answer.raters_count)

def Answer_to_NDBAnswer(answer):
	return create_NDBAnswer(answer.answer, answer.definition, \
								answer.source, answer.total_stars, answer.raters_count)

def initialize_ndb():
	app = webapp2.get_app()
	if 'ndb initialized' not in app.registry:
		text_to_database()
		app.registry['ndb initialized'] = 1	

def create_NDBAnswer(answer, definition, source, total_stars, raters_count):
	return NDBAnswer(answer=urllib.quote(fix_encoding(answer)), \
					 definition=urllib.quote(fix_encoding(definition)), \
					 source=urllib.quote(fix_encoding(source)), \
					 total_stars=total_stars, \
                     raters_count=raters_count)
    
def add_to_ndb(definition, answer, source, total_stars, raters_count):
	if not entry_exists(definition, answer):
		entry = create_NDBAnswer(answer, definition, source, total_stars, raters_count)
		entry.put()

def text_to_database():
	# """reads the entities from solver.defs_to_sols and store them in ndb"""
	defs = ''
	ls = []
	with open(r'definitions.txt', 'rb') as f:
		defs = f.read()

	defs_to_sols = {l.split('-')[0].strip(): map(str.strip, l.split('-')[1].split(';')) for l in defs.split('\n')[:-1]}
	if entry_exists(defs_to_sols.items()[0][0], defs_to_sols.items()[0][1][0]):
		return

	for definition in defs_to_sols:
		for sol in defs_to_sols[definition]:
			entry = create_NDBAnswer(sol, definition, "תשבצל'ה", 5, 1)
			ls.append(entry)
 	ndb.put_multi(ls)

def find_in_ndb(definition, guess):
	'''Returns a list of Answers to definition that match guess'''
	qry = NDBAnswer.query(NDBAnswer.definition == urllib.quote(fix_encoding(definition)))
	answers = filter(lambda x: guess.match(x.answer),\
					map(NDBAnswer_to_Answer, qry.fetch()))
	return sorted(list(set(answers)), key=lambda ans: 1.0 * ans.total_stars / ans.raters_count, reverse=True)

def rate_to_ndb(definition, answer, rate, prev_rate=0, source=SOLVER_NAME):
    if rate not in xrange(1, 6):
        return False
    tmp_answer = create_NDBAnswer(fix_encoding(answer), fix_encoding(definition), '', 0, 1)
    entities = NDBAnswer.query(ndb.AND(NDBAnswer.answer == tmp_answer.answer, NDBAnswer.definition == tmp_answer.definition))
    if entities.get() == None:
        add_to_ndb(definition, answer, source, rate, 1)
        return True
    entity = entities.get()
    if prev_rate > 0:
        entity.total_stars -= prev_rate
        entity.raters_count -= 1
    entity.total_stars += rate
    entity.raters_count += 1
    entity.put()
    return False
    
def entry_exists(definition, answer):
	tmp_answer = create_NDBAnswer(fix_encoding(answer), fix_encoding(definition), '', 0, 1)
	entities = NDBAnswer.query(ndb.AND(NDBAnswer.answer == tmp_answer.answer, \
									 NDBAnswer.definition == tmp_answer.definition))
	return entities.get() != None
