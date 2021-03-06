# -*- coding: utf-8 -*-

import cgi
import re
import json
import urllib
import recentActivityUtils
from encodingUtils import fix_encoding
from google.appengine.ext import ndb

MAX_QUESTIONS_TO_SHOW = 10

class Comment(ndb.Model):
    """Represents a Comment in a forum question."""
    name = ndb.StringProperty(indexed=False)
    answer = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    commentID = ndb.IntegerProperty()
    
    @staticmethod
    def create(name, answer, description, commentID):
        """Creates a Comment with given values"""
        return Comment(name=fix_encoding(name),\
            answer=fix_encoding(answer),\
            description=fix_encoding(description),\
            commentID=commentID)

class Question(ndb.Model):
    """Represents a forum question."""
    name = ndb.StringProperty(indexed=False)
    question = ndb.StringProperty(indexed=False)
    pattern = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    comments = ndb.StructuredProperty(Comment, indexed=False, repeated=True)
    questionID = ndb.IntegerProperty()
    
    @staticmethod
    def create(name, question, pattern, description, questionID):
        """Creates a Question with given values"""
        return Question(name=fix_encoding(name),\
            question=fix_encoding(question),\
            pattern=fix_encoding(pattern),\
            description=fix_encoding(description),\
            comments = [],\
            questionID=questionID)

    def get_question_comments(self):
        """return list of the comments of the question as a tuple (name,answer,desc)."""
        return map(lambda x: (x.name,x.answer,x.description),self.comments)

def get_raw_questions_feed():
    """return the latest MAX_QUESTIONS_TO_SHOW questions in the forum currently."""
    return Question.query().order(-Question.questionID).fetch(MAX_QUESTIONS_TO_SHOW)
    
def get_questions_feed():
    """return the latest MAX_QUESTIONS_TO_SHOW questions in the forum currently in the format of [name,question,pattern,desc,comments,urlsafe]."""
    return map(lambda x:[x.name,
                         x.question,
                         x.pattern,
                         x.description,
                         x.get_question_comments(),
                         x.key.urlsafe()], get_raw_questions_feed())

def add_question(name, question, pattern, description):
    """Creates and adds a question to the DB."""
    name = ' '.join(name.split())
    if (name==''):
        name = 'אנונימי'
    questions = get_raw_questions_feed()
    new_question = Question.create(name, question, pattern, description, 1 + max(map(lambda x:x.questionID,questions)) if questions else 0)
    new_question.put()
    recentActivityUtils.add_ra(recentActivityUtils.NEW_QUESTION_TYPE, [name, question, pattern])
    return [new_question] + questions

def good_answer(pattern,answer):
    """returns true iff answer match the given pattern."""
    return len(pattern) == len(answer) and all(pattern[i] == answer[i] for i in range(len(pattern)) if pattern[i] != '?')

def add_comment(QuestionURL, name, answer, description):
    """Creates and adds a comment to the question specified by urlsafe QuestionURL."""
    name = ' '.join(name.split())
    if (name==''):
        name = 'אנונימי'
    question = ndb.Key(urlsafe=QuestionURL).get()
    description = description.strip()
    if len(description) != 0:
        description = '"'+description+'"'
    if good_answer(question.pattern,answer):
        comments = question.comments
        new_comment = Comment.create(name,answer,description, 1 + max(map(lambda x:x.commentID,comments)) if comments else 0)
        question.comments.append(new_comment)
        question.put()
        return True
    return False