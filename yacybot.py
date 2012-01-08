#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# vim: ts=2 sw=2 expandtab

# ----------------------------------------------------------------------------
LICENSE = \
u""""THE PIZZA-WARE LICENSE" (derived from "THE BEER-WARE LICENCE"):
<cfr34k-yacy@tkolb.de> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a pizza in return. - Thomas Kolb"""
# ----------------------------------------------------------------------------

from ircbot import *
from irclib import irc_lower, nm_to_n
from threading import Timer
import string
import re
import sys
import time
import traceback
import html2text

from YaCyQuery import YaCyQuery

from config import *

class YaCyBot(SingleServerIRCBot):
  def __init__(self, channel, nickname, server, port=6667):
    print "initializing... ",
    SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
    self.channel = channel
    self.last_msg_time = 0
    self.last_query = None
    print "done"

  def on_nicknameinuse(self, c, e) :
    c.nick(c.get_nickname() + "_")
    s = string.join(["nickname", c.get_nickname(), "in use, add '_'"])
    print s

  def on_welcome(self, c, e) :
    print u"joining ", self.channel
    c.join(self.channel)

  def on_pubmsg(self, c, e) :
    nick = nm_to_n(e.source())
    message = e.arguments()[0]

    # messages starting with a '!' are considered bot requests
    if message[0] == '!':
      # split message in command (first word) and parameters
      command_parts = message[1:].split(" ")
      command = command_parts[0]
      if len(command_parts) > 1:
        params = command_parts[1:]
      else:
        params = []

      print "Executing command:", message[1:]

      # interpret the commands
      if command == 'y' or command == 'yacy':
        # build and send the query
        try:
          querystr = " ".join(params);
          query = YaCyQuery(querystr)
          numresults = query.request()

          if numresults == 0:
            self.send_msg(c, self.channel, nick + ": No results for your query \"" + querystr + "\":")
          else:
            numtotalresults = query.getNumTotalResults()
            self.last_query = query

            # print the results
            self.send_msg(c, self.channel, nick + ": The first " + str(numresults) + " results (" + str(numtotalresults) + " total) for your query \"" + querystr + "\":")

            for i in range(numresults):
              result = query.getResult(i)
              self.send_msg(c, self.channel, str(i) + ": " + result['link'])
        except Exception as ex:
          traceback.print_last()
          self.send_msg(c, self.channel, "Oops, an error occurred while processing the request:")
          self.send_msg(c, self.channel, str(ex))


      elif command == 'd' or command == 'details':
        # check for some errors
        if not self.last_query:
          self.send_msg(c, self.channel, "No search was requested yet or no results where returned.")
        elif len(params) < 1:
          self.send_msg(c, self.channel, "!details requires the result index as parameter.")
        elif int(params[0]) >= self.last_query.getNumResults():
          self.send_msg(c, self.channel, "Index is out of range (only " + str(self.last_query.getNumResults()) + " results found).")
        else:
          # everything ok -> show the requested result's details
          resultIndex = int(params[0])
          result = self.last_query.getResult(resultIndex)

          # clean up the description
          description = html2text.html2text(result['description'])

          # show the results
          self.send_msg(c, self.channel, "Title: " + result['title'])
          self.send_msg(c, self.channel, "URL:   " + result['link'])
          self.send_msg(c, self.channel, "Date:  " + result['pubDate'])
          self.send_msg(c, self.channel, "Size:  " + result['sizename'])
          self.send_msg(c, self.channel, "Description: " + description)

      elif command == 'l' or command == 'license':
        self.send_multiline(c, self.channel, LICENSE)
      elif command == 'h' or command == 'help':
        self.send_multiline(c, self.channel, u"""Here are the commands I understand:
!help            - Show this help
!yacy <keywords> - Search for <keywords>
!details <N>     - Print more details for the Nth result from the last query
!license         - Show the license for this program
Every command can be abbreviated with a single letter (i.e. !h for !help)""")
      else:
        self.send_msg(c, self.channel, nick + u": I don't know what you mean. Please ask for !help ;-)")

  def on_privmsg(self, c, e) :
      nick = nm_to_n(e.source())
      message = e.arguments()[0].decode('utf-8')

      if nick in self._active_users:
        self._answers[nick].append(message)

  # send a message and wait for some time to bypass flood protection
  def send_msg(self, c, target, msg):
    sleep_time = IRC_MIN_DELAY - (time.time() - self.last_msg_time)

    c.privmsg(target, msg.encode('utf-8'))

    if sleep_time > 0:
      time.sleep(sleep_time)

    self.last_msg_time = time.time()

  # send a "multiline" message by splitting it into single line messages
  def send_multiline(self, c, target, msg):
    lines = msg.split("\n")
    for line in lines:
      self.send_msg(c, target, line);

  # show a simple progress bar
  def progressbar(self, progress):
    split_point = 50 * progress
    str = ""
    for i in range(50):
      if i < split_point:
        str = str + "#"
      else:
        str = str + "-"

    return str

def main() :
  print "starting up..."

  bot = YaCyBot(IRC_CHANNEL, IRC_NICK, IRC_SERVER, IRC_PORT)
  bot.start()

if __name__ == "__main__" :
  main()
