#!/usr/bin/env python

from google.appengine.ext import db

class Countable(db.Model):
  count = db.IntegerProperty()

class Date(Countable):
  date = db.DateProperty()

class Hour(Countable):
  hour = db.IntegerProperty()

class Year(Countable):
  year = db.IntegerProperty()

class Author(Countable):
  name = db.StringProperty()
  email = db.StringProperty()

class Subject(Countable):
  subject = db.StringProperty()

class Tag(Countable):
  tag = db.StringProperty()

class Message(db.Model):
  subject = db.ReferenceProperty(reference_class=Subject,
                                 collection_name='messages')
  date = db.ReferenceProperty(reference_class=Date,
                              collection_name='messages')
  hour = db.ReferenceProperty(reference_class=Hour,
                              collection_name='messages')
  year = db.ReferenceProperty(reference_class=Year,
                              collection_name='messages')
  author = db.ReferenceProperty(reference_class=Author,
                                collection_name='messages')
  tag = db.ReferenceProperty(reference_class=Tag,
                             collection_name='messages')
