# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import sys
import os
import fnmatch
import pprint
import tkinter as tk
from functools import partial

import musicplayer

from .constants import CLIENT_NAME
from .data import Song
from .client import Client

# FFmpeg log levels: {0:panic, 8:fatal, 16:error, 24:warning, 32:info, 40:verbose}
musicplayer.setFfmpegLogLevel(20)


def songs():
    global i, files
    while True:
        yield Song(files[i])
        i += 1
        if i >= len(files):
            i = 0


def peek_songs(n):
    nexti = i + 1
    if nexti >= len(files):
        nexti = 0
    return map(Song, (files[nexti:] + files[:nexti])[:n])


class App(object):
    def __init__(self):
        # Create our Music Player.
        self.player = musicplayer.createPlayer()
        self.player.outSamplerate = 96000  # support high quality :)

        # Create our Jellyfin Client.
        self.client = Client()

    def run(self):
        # self.player.queue = songs()
        # self.player.peekQueue = peek_songs
        # self.player.playing = True

        # Setup a simple GUI.
        root = tk.Tk()
        root.title(CLIENT_NAME)
        if not self.client.connect():
            win = self.connection_window(root)
        else:
            win = self.player_window(root)
        albums = self.client.get_latest_albums()
        songs = self.client.get_album_songs(albums[0])
        root.mainloop()
        self.client.stop()

    def player_window(self, master):
        frame = tk.Frame(master)
        songLabel = tk.StringVar()

        def onSongChange(
            **kwargs): songLabel.set(pprint.pformat(self.player.curSongMetadata))

        def cmdPlayPause(*args): self.player.playing = not self.player.playing
        def cmdNext(*args): self.player.nextSong()

        tk.Label(frame, textvariable=songLabel).pack()
        tk.Button(frame, text="Play/Pause", command=cmdPlayPause).pack()
        tk.Button(frame, text="Next", command=cmdNext).pack()

        self.player.onSongChange = onSongChange
        # self.player.playing = True # start playing
        frame.pack()


    def connection_window(self, master):
        frame = tk.Frame(master)
        def log_in(host, username, password):
            frame.destroy()
            if not self.client.log_in(host.get(), username.get(), password.get()):
                self.connection_window(master, self.client)
            else:
                self.player_window(master)

        # Host
        hostLabel = tk.Label(frame, text="Host").pack()
        host = tk.StringVar()
        hostEntry = tk.Entry(frame, textvariable=host).pack()
        # Username
        usernameLabel = tk.Label(frame, text="Username").pack()
        username = tk.StringVar()
        usernameEntry = tk.Entry(frame, textvariable=username).pack()
        # Password
        passwordLabel = tk.Label(frame, text="Password").pack()
        password = tk.StringVar()
        passwordEntry = tk.Entry(frame, textvariable=password, show='*').pack()
        # Submit
        submitButton = tk.Button(
            frame, text='Log in', command=partial(log_in, host, username, password)).pack()
        frame.pack()

