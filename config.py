# --- Configuration for YaCyBot ---
# vim: ts=2 sw=2 expandtab

# ----------------------------------------------------------------------------
# "THE PIZZA-WARE LICENSE" (derived from "THE BEER-WARE LICENCE"):
# <cfr34k-yacy@tkolb.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a pizza in return. - Thomas Kolb
# ----------------------------------------------------------------------------

IRC_SERVER  = "localhost" # Hostname / IP of the IRC server
IRC_PORT    = 61234       # Port of the IRC server
IRC_NICK    = "YaCyBot"   # Nick of the bot
IRC_CHANNEL = "#yacytest" # The channel to join

# Increase this if the server drops messages because of flood protection
IRC_MIN_DELAY = 0.8

YACY_ADDRESS     = "localhost" # Hostname / IP of the YaCy-Peer
YACY_PORT        = 8080        # Port of the YaCy-Peer
YACY_NUM_RESULTS = 5           # Maximum number of results to show for each
                               # query
