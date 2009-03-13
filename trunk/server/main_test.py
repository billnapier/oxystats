#!/usr/bin/python

import unittest

# Pull in AppEngine sdk (mac location)
import sys
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")

from datetime import timedelta
import datetime

import main as main_module

class MainTest(unittest.TestCase):
    def testConvertWhenToDateAllTime(self):
        self.assertEqual(main_module.ConvertWhenToDate('alltime'),
                         None)

    def testConvertWhenToDateToday(self):
        today = datetime.date.today()
        self.assertEqual(main_module.ConvertWhenToDate('today'),
                         today)
        self.assertEqual(main_module.ConvertWhenToDate('TODAY'),
                         today)
        self.assertEqual(main_module.ConvertWhenToDate('tOdaY'),
                         today)

    def testConvertWhenToDateYesterday(self):
        yesterday = datetime.date.today() - timedelta(days=1)
        self.assertEqual(main_module.ConvertWhenToDate('yesterday'),
                         yesterday)
        self.assertEqual(main_module.ConvertWhenToDate('YESTERDAY'),
                         yesterday)
        self.assertEqual(main_module.ConvertWhenToDate('yESteRDay'),
                         yesterday)

    def testConvertWhenToDateExactDate(self):
        when = datetime.date(1976, 4, 4)
        self.assertEqual(main_module.ConvertWhenToDate('4-4-1976'),
                         when)
        self.assertEqual(main_module.ConvertWhenToDate('4/4/1976'),
                         when)
        when = datetime.date(1975, 1, 21)
        self.assertEqual(main_module.ConvertWhenToDate('1-21-1975'),
                         when)
        self.assertEqual(main_module.ConvertWhenToDate('1/21/1975'),
                         when)

if __name__ == '__main__':
    unittest.main()
