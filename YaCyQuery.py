#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# vim: ts=2 sw=2 expandtab

# ----------------------------------------------------------------------------
# "THE PIZZA-WARE LICENSE" (derived from "THE BEER-WARE LICENCE"):
# <cfr34k-yacy@tkolb.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a pizza in return. - Thomas Kolb
# ----------------------------------------------------------------------------

import urllib, urllib2
import json
import re

from config import *

# This class fetches results from a YaCy peer using the JSON interface and
# stores them into a Python list
class YaCyQuery:
  def __init__(self, query):
    # default parameters for the yacy request
    self.urlparams = YACY_DEFAULT_PARAMS
    self.urlparams['query'] = query

    # initalize attributes
    self.results = []
    self.totalresults = 0

    # precompile the number cleanup pattern
    self.numbercleanup = re.compile('[^0-9]+')

  # A safe (i.e. exception-free) function for casting numeric strings to
  # integer
  def _safe_cast_int(self, numstr):
    try:
      return int(numstr)
    except ValueError:
      return -1

  # add or change an URL parameter
  def setParam(self, key, value):
    self.urlparams[key] = value

  # change the query string
  def setQuery(self, query):
    self.urlparams['query'] = query

  # send the request and save the result
  def request(self):
    data = urllib.urlencode(self.urlparams)
    url = 'http://' + YACY_ADDRESS + ':' + str(YACY_PORT) + '/yacysearch.json'

    # open the URL
    urlobj = urllib2.urlopen(url, data)

    # get the JSON data
    jsondata = urlobj.read()

    # decode the JSON data
    jsonobj = json.loads(jsondata)

    # remove non-numeric characters from the total number of results
    cleanedtotal = self.numbercleanup.sub('', jsonobj['channels'][0]['totalResults'])

    # store the relevant data in class members
    self.totalresults = self._safe_cast_int(cleanedtotal)
    self.results = jsonobj['channels'][0]['items']

    return len(self.results)

  def getResult(self, index):
    return self.results[index]

  def getResultList(self):
    return self.results

  def getNumResults(self):
    return len(self.results)

  def getNumTotalResults(self):
    return self.totalresults

if __name__ == "__main__" :
  # simple class test
  query = YaCyQuery('yacy')
  numresults = query.request()

  print "Showing first", numresults, "of", query.getNumTotalResults(), "results"

  for i in range(numresults):
    result = query.getResult(i)
    print str(i) + ": " + result['link']
