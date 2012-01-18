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
import xml.dom.minidom
import time

from config import *

# This class fetches results from a YaCy peer using the JSON interface and
# stores them into a Python list
class YaCyStats:
  def __init__(self):
    self.peers = 0
    self.allURLs = 0
    self.allRWIs = 0
    self.allPPM = 0
    self.allQPH = 0

    self.myName = ''
    self.myURLs = 0
    self.myRWIs = 0

    self.lastUpdate = 0
    pass

  # Extracts all text in a list of DOM nodes
  def _getText(self, nodelist):
    rc = []
    for node in nodelist:
      if node.nodeType == node.TEXT_NODE:
        rc.append(node.data)
    return ''.join(rc)

  # Update the cached statistics data.
  # Returns True if the data was refreshed, False if the cached version is
  # still used.
  def update(self):
    curTime = time.time()

    if curTime - self.lastUpdate < YACY_STATS_UPDATE_INTERVAL*1000:
      return False

    url = 'http://' + YACY_ADDRESS + ':' + str(YACY_PORT) + '/Network.xml'

    # open the URL
    urlobj = urllib2.urlopen(url, timeout = URLLIB_TIMEOUT)

    # get the XML data
    xmldata = urlobj.read()

    # parse the XML data into a DOM model
    dom = xml.dom.minidom.parseString(xmldata);

    # store the relevant data in class members
    peers = dom.getElementsByTagName('peers')[0]

    activePeers = peers.getElementsByTagName('active')[0]
    self.peers = int(self._getText(activePeers.getElementsByTagName('count')[0].childNodes))
    self.allURLs = int(self._getText(activePeers.getElementsByTagName('links')[0].childNodes))
    self.allRWIs = int(self._getText(activePeers.getElementsByTagName('words')[0].childNodes))

    cluster = peers.getElementsByTagName('cluster')[0]
    self.allPPM = int(self._getText(cluster.getElementsByTagName('ppm')[0].childNodes))
    self.allQPH = float(self._getText(cluster.getElementsByTagName('qph')[0].childNodes))

    yourPeer = peers.getElementsByTagName('your')[0]
    self.myName = self._getText(yourPeer.getElementsByTagName('name')[0].childNodes)
    self.myURLs = int(self._getText(yourPeer.getElementsByTagName('links')[0].childNodes))
    self.myRWIs = int(self._getText(yourPeer.getElementsByTagName('words')[0].childNodes))

    return True

if __name__ == "__main__" :
  # simple class test
  stats = YaCyStats()

  stats.update()

  print "Number of Peers:", stats.peers
  print "Peer name:", stats.myName
