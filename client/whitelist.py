#!/usr/bin/python

import sys
import getpass
from optparse import OptionParser

# Pull in AppEngine sdk (mac location)
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")

# Pull in server parts
sys.path.append("../server")

from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext import db
import model
import yaml

parser = OptionParser()
parser.add_option('-d', '--debug',
                  action='store_true',
                  dest='debug',
                  help='talk to debug instance instead of prod instance')
parser.add_option('-u', '--user', action='store', dest='username',
                  help='username to authenticate with')
parser.add_option('-p', '--pass', action='store', dest='password',
                  help='password to authenticate with')
parser.add_option('-a', '--appid',
                  dest='appid',
                  help='AppEngine appid to talk to')
(options, args) = parser.parse_args()

if options.username is None:
    print 'username is a required parameter'
    sys.exit()
username = options.username

if options.appid is None:
    fp = file('../server/app.yaml', 'r')
    app = yaml.load(fp)
    app_id = app['application']
else:
    app_id = options.appid

if options.password is None:
    password = getpass.getpass()
else:
    password = options.password

if options.debug:
    host = 'localhost:8087'
else:
    host = app_id + '.appspot.com'

remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', lambda: (username, password), host)

# Whitelist an e-mail address by creating a user entry with no posts.
try:
    (email, name) = args
    author = model.Author.get_or_insert(key_name='key:%s' % email,
                                        name=name,
                                        email=email,
                                        count=0)
    author.put()
except:
    print "whitelist.py email name"
