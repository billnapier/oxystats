#!/usr/bin/env python

import datetime
import gviz_api
import heapq
import logging
import model
import os
import wsgiref.handlers

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

def check_if_valid_user():
  """Make sure the user is one we have in the system.

  Returns:
    True if valid user.
  """
  user = users.get_current_user()
  # This means that we forgot to protect a page
  if user is None:
    logging.error('got null current user...')
    return False
  value = model.Author.get_by_key_name('key:%s' % user.email().lower()) is not None
  if not value:
    logging.debug('don\'t know: ' + user.email())
  return value

def ConvertWhenToDate(when):
  if when.lower() == 'alltime':
    return None
  if when.lower() == 'today':
    return datetime.date.today()
  if when.lower() == 'yesterday':
    return datetime.date.today() - datetime.timedelta(days=1)
  try:
    (month, day, year) = when.split('-')
  except ValueError:
    (month, day, year) = when.split('/')
  return datetime.date(int(year), int(month), int(day))

def ParseQueryParmas(request):
    limit = int(request.get('limit', '10'))
    offset = int(request.get('offset', '0'))
    order = request.get('order', 'desc').lower()
    if order != 'desc' or order != 'asc':
      order = 'desc'
    when = ConvertWhenToDate(request.get('when', 'alltime'))
    return (limit, offset, order, when)

class DataHandler(webapp.RequestHandler):
  def GetTqx(self):
    tqx = self.request.get("tqx")
    if tqx is None:
      tqx = ''
    return tqx


class ByTagHandler(DataHandler):
  def get(self):
    if not check_if_valid_user():
      self.response.out.write("I don't know you")
      return
    description = dict(tag=("string", "Tag"),
                       messages=("number", "Messages"))
    data_table = gviz_api.DataTable(description)
    data = []

    (limit, offset, order, when) = ParseQueryParmas(self.request)

    if when is None:
      query = model.Tag.gql('ORDER BY count %s' % order)
      for tag in query.fetch(limit, offset):
        data_table.AppendData([dict(tag=tag.tag,
                                    messages=tag.count)])
    else:
      ByDayHelper(when, order, limit, data_table, 'tag',
                  key=lambda msg: msg.tag.tag)

    self.response.out.write(data_table.ToResponse(columns_order=("tag", "messages"),
                                                  order_by=("messages", order),
                                                  tqx=self.GetTqx()))

class BySubjectHandler(DataHandler):
  def get(self):
    if not check_if_valid_user():
      self.response.out.write("I don't know you")
      return
    description = dict(subject=("string", "Subject"),
                       messages=("number", "Messages"))
    data_table = gviz_api.DataTable(description)
    data = []

    (limit, offset, order, when) = ParseQueryParmas(self.request)

    if when is None:
      query = model.Subject.gql('ORDER BY count %s' % order)
      for subject in query.fetch(limit, offset):
        data_table.AppendData([dict(subject=subject.subject,
                                    messages=subject.count)])
    else:
      ByDayHelper(when, order, limit, data_table, 'subject',
                         key=lambda msg: msg.subject.subject)

    self.response.out.write(data_table.ToResponse(columns_order=("subject", "messages"),
                                                  order_by=("messages", order),
                                                  tqx=self.GetTqx()))

def ByDayHelper(when, order, limit, data_table, key_name, key):
  dateStr = when.strftime("%m/%d/%Y")
  date = model.Date.get_by_key_name('key:%s' % dateStr)
  if date is None:
    # No data for that day
    return []
  msgs = date.messages.fetch(1000)
  results=dict()
  for msg in msgs:
    subject = key(msg)
    count = results.get(subject, 0)
    results[subject] = count + 1
  data = []
  if order == 'asc':
    tmp_data = heapq.nsmallest(limit, results.items(), key=lambda x: x[1])
  else:
    tmp_data = heapq.nlargest(limit, results.items(), key=lambda x: x[1])
  for d in tmp_data:
    if data_table is None:
      data.append({key_name: d[0],
                   'messages': d[1]})
    else:
      data_table.AppendData([{key_name: d[0],
                              'messages': d[1]}])
  return data

def GetAuthorStats(author, count):
  oldest_msg = model.Message.gql('WHERE author = :1 ORDER BY __key__ ASC', author).get()
  if oldest_msg is None:
    logging.debug("couldn't find oldest msg for " + author.email)
    return dict()
  daysonoxy = (datetime.date.today() - oldest_msg.date.date).days
  avg_posts_per_day = float(author.count) / float(daysonoxy)
  return dict(email=author.email,
              name=author.name,
              firstpost=oldest_msg.date.date,
              daysonoxy=daysonoxy,
              avg_posts_per_day=avg_posts_per_day,
              messages=count)

class ByAuthorHandler(DataHandler):
  def get(self):
    if not check_if_valid_user():
      self.response.out.write("I don't know you")
      return
    description = dict(email=("string", "Email"),
                       name=("string", "Name"),
                       firstpost=("date", "First Post Date"),
                       daysonoxy=("number", "Days on Oxy"),
                       avg_posts_per_day=("number", "Average Posts Per Day"),
                       messages=("number", "Messages"))
    data_table = gviz_api.DataTable(description)

    (limit, offset, order, when) = ParseQueryParmas(self.request)

    if when is None:
      # count == 0 people are whitelisted entries.
      query = model.Author.gql('WHERE count > 0 ORDER BY count %s' % order)
      for author in query.fetch(limit, offset):
        data_table.AppendData([GetAuthorStats(author, author.count)])
    else:
      data = ByDayHelper(when, order, limit, None, 'email',
                         key=lambda msg: msg.author.email)
      for d in data:
        author = model.Author.get_by_key_name('key:%s' % d['email'])
        d.update(GetAuthorStats(author, d['messages']))
        data_table.LoadData(data)

    self.response.out.write(data_table.ToResponse(columns_order=("email", "name", "messages", "firstpost", "daysonoxy", "avg_posts_per_day"),
                                                  order_by=("messages", order),
                                                  tqx=self.GetTqx()))

class ByHourHandler(DataHandler):
  def get(self):
    if not check_if_valid_user():
      self.response.out.write("I don't know you")
      return
    description = dict(hour=("number", "Hour"),
                       hour_est=("number", "Hour (EST)"),
                       hour_str=("string", "Hour"),
                       hour_est_str=("string", "Hour (EST)"),
                       messages=("number", "Messages"))
    data_table = gviz_api.DataTable(description)
    data = []
    for hour in model.Hour.all():
      hour_est = hour.hour - 5
      if hour_est < 0:
        hour_est = 24 + hour_est

      data_table.AppendData([dict(hour=hour.hour,
                                  hour_str=str(hour.hour),
                                  hour_est=hour_est,
                                  hour_est_str=str(hour_est),
                                  messages=hour.count)])

    self.response.out.write(data_table.ToResponse(columns_order=("hour_est_str", "hour_str", "messages"),
                                                  tqx=self.GetTqx()))

class ByDayHandler(DataHandler):
  def get(self):
    if not check_if_valid_user():
      self.response.out.write("I don't know you")
      return

    tqx_dict = gviz_api.ParseTqx(self.GetTqx())
    tqx_out = tqx_dict.get("out", "json")
    response = memcache.get('by_day_' + tqx_out)
    if response is not None:
      if tqx_out != 'json':
        self.response.out.write(response)
        return
      else:
        self.response.out.write(response % tqx_dict.get("reqId", 0))
        return

    description = dict(day=("date", "Day"),
                       messages=("number", "Messages"))
    data_table = gviz_api.DataTable(description)

    for day in model.Date.all():
      data_table.AppendData([dict(day=day.date,
                                 messages=day.count)])

    if tqx_out != 'json':
      response = data_table.ToResponse(columns_order=("day", "messages"),
                                                  tqx=self.GetTqx())
      # cache for 5 minutes...
      memcache.set('by_day_' + tqx_out, response, 60 * 5)
    else:
      table = data_table.ToJSon(columns_order=("day", "messages"), order_by=())
      response_handler = tqx_dict.get("responseHandler",
                                      "google.visualization.Query.setResponse")
      response = ("%s({'version':'0.5', 'reqId':'%%s', 'status':'OK', "
              "'table': %s});") % (response_handler, table)
      # cache for 5 minutes...
      memcache.set('by_day_' + tqx_out, response, 60 * 5)

      response = response % tqx_dict.get("reqId", 0)

    self.response.out.write(response)

class ForAuthorHandler(webapp.RequestHandler):
  def get (self):
    email = self.request.get('email', None)
    if email is None:
      self.redirect('/')

    author = model.Author.get_by_key_name('key:%s' % email)
    first_msg = model.Message.gql('WHERE author = :1 ORDER BY __key__ ASC', author).get()
    last_msg = model.Message.gql('WHERE author = :1 ORDER BY __key__ DESC', author).get()

    self.response.out.write('hi %s<BR>' % author.name)
    self.response.out.write('First Post: %s<br>' % first_msg.date.date)
    self.response.out.write('Latest Post: %s<br>' % last_msg.date.date)

class MainHandler(webapp.RequestHandler):
  def get(self):
    if check_if_valid_user():
      self.redirect('index.html')
    else:
      self.response.out.write("I don't know you.")

class ErrorHandler(webapp.RequestHandler):
  def get(self):
    self.redirect('/')

def GetTemplate(name):
  return os.path.join(os.path.dirname(__file__), 'templates', name)

class StaticHandler(webapp.RequestHandler):
  def get(self):
    if check_if_valid_user():
      path = GetTemplate(self.request.path[1:])
      when = self.request.get('when', 'alltime')
      limit = self.request.get('limit', '10')
      if when == 'alltime':
        pretty_when = 'All Time'
      else:
        pretty_when = ConvertWhenToDate(when).strftime("%m-%d-%Y")
      template_values = dict(when=when,
                             limit=limit,
                             pretty_when=pretty_when)
      self.response.out.write(template.render(path, template_values))
    else:
      self.response.out.write("I don't know you.")

def main():
  application = webapp.WSGIApplication([('/data_by_tag', ByTagHandler),
                                        ('/data_by_subject', BySubjectHandler),
                                        ('/data_by_hour', ByHourHandler),
                                        ('/data_by_author', ByAuthorHandler),
                                        ('/data_by_day', ByDayHandler),
                                        ('/data_for_author', ForAuthorHandler),
                                        ('/index.html', StaticHandler),
                                        ('/script.js', StaticHandler),
                                        ('/', MainHandler),
                                        ('.*', ErrorHandler),
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
