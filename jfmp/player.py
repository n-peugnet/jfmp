# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import sys
import os
import fnmatch
import pprint
import tkinter as Tkinter

import musicplayer

from jfmp.constants import CLIENT_NAME

# FFmpeg log levels: {0:panic, 8:fatal, 16:error, 24:warning, 32:info, 40:verbose}
musicplayer.setFfmpegLogLevel(20)


class Song:
    def __init__(self, fn):
        self.url = fn
        self.f = open(fn, "rb")

    def __eq__(self, other):
        return self.url == other.url

    def readPacket(self, bufSize):
        s = self.f.read(bufSize)
        # print "readPacket", self, bufSize, len(s)
        return s

    def seekRaw(self, offset, whence):
        r = self.f.seek(offset, whence)
        # print "seekRaw", self, offset, whence, r, self.f.tell()
        return self.f.tell()


files = []


def get_files(path):
    for f in sorted(os.listdir(path)):
        f = os.path.join(path, f)
        if os.path.isdir(f):
            get_files(f)  # recurse
        if len(files) > 1000:
            break  # break if we have enough
        if fnmatch.fnmatch(f, '*.mp3'):
            files.append(f)


get_files(os.path.expanduser("~/Music"))
files = sys.argv[1:] + files
assert files, "give me some files or fill-up ~/Music"

i = 0


def songs():
    global i, files
    while True:
        yield Song(files[i])
        i += 1
        if i >= len(files): i = 0


def peek_songs(n):
    nexti = i + 1
    if nexti >= len(files): nexti = 0
    return map(Song, (files[nexti:] + files[:nexti])[:n])

class Player(object):

    def start(self):
        # Create our Music Player.
        player = musicplayer.createPlayer()
        player.outSamplerate = 96000 # support high quality :)
        player.queue = songs()
        player.peekQueue = peek_songs
        player.playing = True


        # Setup a simple GUI.
        window = Tkinter.Tk()
        window.title(CLIENT_NAME)
        songLabel = Tkinter.StringVar()

        def onSongChange(**kwargs): songLabel.set(pprint.pformat(player.curSongMetadata))
        def cmdPlayPause(*args): player.playing = not player.playing
        def cmdNext(*args): player.nextSong()

        Tkinter.Label(window, textvariable=songLabel).pack()
        Tkinter.Button(window, text="Play/Pause", command=cmdPlayPause).pack()
        Tkinter.Button(window, text="Next", command=cmdNext).pack()

        player.onSongChange = onSongChange
        player.playing = True # start playing
        window.mainloop()