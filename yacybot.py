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
from YaCyStats import YaCyStats

from config import *

class YaCyBot(SingleServerIRCBot):
  def __init__(self, channel_list, nickname, server, port=6667):
    print "initializing... ",
    SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
    self.channels_to_join = channel_list

    self.last_msg_time = 0 # timestamp of the last message sent, so the next
                           # one can be delayed, if necessary

    self.last_queries = {} # this stores the last query for everyone who asks
                           # about results (i.e. channels and queries)

    self.stats = YaCyStats() # Object for statistics about the YaCy network

    self.ping_timer = None # handle of the client->server ping timer
    self.ping_channel = channel_list[0] # name of the ping target

    print "done"

  def on_nicknameinuse(self, c, e) :
    c.nick(c.get_nickname() + "_")
    s = string.join(["nickname", c.get_nickname(), "in use, add '_'"])
    print s

  def on_welcome(self, c, e) :
    # clear the last-query list
    self.last_queries = {}

    # join all the channels
    for channel in self.channels_to_join:
      print u"joining ", channel
      c.join(channel)

    # stop the old ping timer, if one is running
    if self.ping_timer:
      self.ping_timer.cancel()

    # start the new one
    if IRC_PING_INTERVAL != 0:
      # ping the first joined channel for keep-alive
      self.ping_timer = Timer(IRC_PING_INTERVAL, self.send_ping, [c])
      self.ping_timer.start()

  def on_pubmsg(self, c, e) :
    # process messages from the joined channels
    nick = nm_to_n(e.source())
    channel = e.target()
    message = e.arguments()[0]

    self.process_message(c, nick, channel, message, True)

  def on_privmsg(self, c, e) :
    # process messages from queries
    nick = nm_to_n(e.source())
    message = e.arguments()[0]

    self.process_message(c, nick, nick, message, False)

  def process_message(self, c, nick, reply_to, message, is_public = True):
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

      if is_public:
        highlight_str = nick + ": "
      else:
        highlight_str = ""

      # interpret the commands
      if command == 'y' or command == 'yacy':
        # build and send the query
        try:
          querystr = " ".join(params);
          query = YaCyQuery(querystr)
          numresults = query.request()

          if numresults == 0:
            self.send_msg(c, reply_to, highlight_str + "No results for your query \"" + querystr + "\".")
          else:
            numtotalresults = query.getNumTotalResults()
            self.last_queries[reply_to] = query

            # print the results
            self.send_msg(c, reply_to, highlight_str + "The first " + str(numresults) + " results (" + str(numtotalresults) + " total) for your query \"" + querystr + "\":")

            for i in range(numresults):
              result = query.getResult(i)
              self.send_msg(c, reply_to, str(i) + ": " + result['link'])
        except Exception as ex:
          traceback.print_exc()
          self.send_msg(c, reply_to, "Oops, an error occurred while processing the request:")
          self.send_msg(c, reply_to, str(ex))

      elif command == 'd' or command == 'details':
        # check for some errors
        if not self.last_queries[reply_to]:
          self.send_msg(c, reply_to, "No search was requested yet or no results where returned.")
        elif len(params) < 1:
          self.send_msg(c, reply_to, "!details requires the result index as parameter.")
        elif int(params[0]) >= self.last_queries[reply_to].getNumResults():
          self.send_msg(c, reply_to, "Index is out of range (only " + str(self.last_queries[reply_to].getNumResults()) + " results found).")
        else:
          # everything ok -> show the requested result's details
          resultIndex = int(params[0])
          result = self.last_queries[reply_to].getResult(resultIndex)

          # clean up the description
          description = html2text.html2text(result['description'])

          # show the results
          self.send_msg(c, reply_to, "Title: " + result['title'])
          self.send_msg(c, reply_to, "URL:   " + result['link'])
          self.send_msg(c, reply_to, "Date:  " + result['pubDate'])
          self.send_msg(c, reply_to, "Size:  " + result['sizename'])
          self.send_msg(c, reply_to, "Description: " + description)

      elif command == 's' or command == 'stats':
        self.stats.update()

        # show the results
        self.send_msg(c, reply_to, "Queried peer's name: " + self.stats.myName)
        self.send_msg(c, reply_to, "RWIs on this peer: " + str(self.stats.myRWIs))
        self.send_msg(c, reply_to, "URLs on this peer: " + str(self.stats.myURLs))
        self.send_msg(c, reply_to, "Number of known active peers: " + str(self.stats.peers))
        self.send_msg(c, reply_to, "URLs on active peers: " + str(self.stats.allURLs))
        self.send_msg(c, reply_to, "RWIs on active peers: " + str(self.stats.allRWIs))
        self.send_msg(c, reply_to, "Cluster PPM: " + str(self.stats.allPPM))
        self.send_msg(c, reply_to, "Cluster QPH: " + str(self.stats.allQPH))

      elif command == 'l' or command == 'license':
        self.send_multiline(c, reply_to, LICENSE)
      elif command == 'h' or command == 'help':
        self.send_multiline(c, reply_to, u"""Here are the commands I understand:
!help            - Show this help
!yacy <keywords> - Search for <keywords>
!details <N>     - Print more details for the Nth result from the last query
!license         - Show the license for this program
Every command can be abbreviated with a single letter (i.e. !h for !help)""")
      else:
        self.send_msg(c, reply_to, highlight_str + "I don't know what you mean. Please ask for !help ;-)")


  def send_ping(self, c):
    # send a /ping command to the server and restart the timer
    c.ping(self.ping_channel);
    self.ping_timer = Timer(IRC_PING_INTERVAL, self.send_ping, [c]);
    self.ping_timer.start();

  def shutdown(self):
    print "shutting down."
    if self.ping_timer:
      self.ping_timer.cancel()
    self.disconnect("Quitting on user request.")

  # send a message and wait for some time to bypass flood protection
  def send_msg(self, c, target, msg):
    sleep_time = IRC_MIN_DELAY - (time.time() - self.last_msg_time)

    try:
      c.privmsg(target, msg.encode('utf-8'))
    except:
      c.privmsg(target, msg)

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

  try:
    bot = YaCyBot(IRC_CHANNELS, IRC_NICK, IRC_SERVER, IRC_PORT)
    bot.start()
  except KeyboardInterrupt:
    bot.shutdown()

if __name__ == "__main__" :
  main()
