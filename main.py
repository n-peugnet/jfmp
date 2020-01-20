#!/usr/bin/env python3
from jfmp.player import Player
from jfmp.client import Client


player_manager = Player()
# player_manager.start()

client_manager= Client()
client_manager.connect()
client_manager.close()