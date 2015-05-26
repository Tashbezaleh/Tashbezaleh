# -*- coding: utf-8 -*-

#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR COsNDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.api import users
from google.appengine.ext import ndb

import urllib
import webapp2, solver, cgi, re, time
import jinja2, os, databaseUtils, cookiesUtils
from encodingUtils import fix_encoding

JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)), extensions=['jinja2.ext.autoescape'],autoescape=True) 

red_font = '<font color="red">%s</font>'
missing_field_message = red_font % 'אנא הכנס %s'

#main page, "/"
class MainHandler(webapp2.RequestHandler):
    def get(self):      
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('/templates/index.html')
        in_text = template.render(template_values)
        self.response.write(in_text)

class ResultsHandler(webapp2.RequestHandler):
    def get(self):
        get_results(self)

class ResultActionHandler(webapp2.RequestHandler):
    def get(self):
        
        definition = cgi.escape(self.request.get('definition'))
        answer = cgi.escape(self.request.get('answer'))
        action = cgi.escape(self.request.get('action'))
        
        #check GET input
        if definition == '':
            self.response.write(missing_field_message % 'הגדרה')
            return
        elif answer == '':
            self.response.write(missing_field_message % 'פתרון')
            return
        elif action == '':
            self.response.write(red_font % 'פעולה לא נתמכת')
            return
        # if not databaseUtils.entry_exists(definition, answer):
        #     databaseUtils.add_to_ndb(definition, answer, databaseUtils.SOLVER_NAME, 0)

       
        was_voted = False
        answer_object = databaseUtils.Answer(answer.encode('utf'), definition.encode('utf'), '', 0)
        if action in ['up', 'down'] and cookiesUtils.can_vote(self, answer_object, action):
            was_voted = databaseUtils.vote_to_ndb(definition, answer, action)
            # if is here to allow users change their votes
            if not cookiesUtils.can_vote(self, answer_object, 'down' if action == 'up' else 'up'):
                cookiesUtils.del_from_cookies(self, answer_object)
            else:
                cookiesUtils.vote_cookie(self, answer_object, action)

        if action == 'add':
            source = cgi.escape(self.request.get('source'))
            if source == '':
                source = 'אנונימי'
            databaseUtils.add_to_ndb(definition, answer, source, 0)
            return self.response.write('תודה על תרומתך')

        get_results(self, was_voted, definition, answer, action)
        



# for admins only, please only enable when testing and db reset is needed
class ResetDBHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("START WORKING <br>")
        ndb.delete_multi(databaseUtils.NDBAnswer.query().fetch(keys_only = True))
        self.response.write("DONE DELETING <br>")
        databaseUtils.initialize_ndb()
        self.response.write("GREAT SUCCESS")

# class TestHandler(webapp2.RequestHandler):
#     def get(self):
#         template = JINJA_ENVIRONMENT.get_template('/templates/test.html')
#         output = template.render({})
#         self.response.write(output)

debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/results.html', ResultsHandler),
    ('/result_action', ResultActionHandler),
    ('/reset_db.html', ResetDBHandler) #,
    # ('/test.html', TestHandler)
], debug=True)



def get_results(this, was_voted=False, changed_definition='', answer='', action=''):
    definition = cgi.escape(this.request.get('definition'))
    pattern = cgi.escape(this.request.get('pattern'))
    
    #check GET input
    if definition == '':
        this.response.write(missing_field_message % 'הגדרה')
        return
    elif pattern == '':
        this.response.write(missing_field_message % 'תבנית')
        return

    regex = solver.user_pat_to_regex(pattern)
    results = []
    #each element in results is of class Answer defined in databaseUtils
    for result in solver.find(fix_encoding(definition), regex):
        if was_voted and fix_encoding(result.definition) == fix_encoding(changed_definition) and \
             fix_encoding(result.answer) == fix_encoding(answer): # getting over ndb being "eventually" consistent
                result.rank += 1 if action == 'up' else -1
        results += [(result, cookiesUtils.can_vote(this, result, 'up'), cookiesUtils.can_vote(this, result, 'down'))]
    # rendering the page with the results
    template_values= {
    'results_list' : results,
    'definition' : definition,
    'pattern' : pattern,
    'result_list_len' : len(results)
    }
    template = JINJA_ENVIRONMENT.get_template('/templates/results.html')
    this.response.write(template.render(template_values))