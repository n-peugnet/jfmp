from typing import List

import musicplayer

from .data import Song

# FFmpeg log levels: {0:panic, 8:fatal, 16:error, 24:warning, 32:info, 40:verbose}
musicplayer.setFfmpegLogLevel(20)

songs = []
i = 0

def get_songs():
    global i, songs
    while True:
        yield songs[i]
        i += 1
        if i >= len(songs):
            i = 0

def peek_songs(n):
    global i, songs
    nexti = i + 1
    if nexti >= len(songs):
        nexti = 0
    return (songs[nexti:] + songs[:nexti])[:n]

class Player():
    def __init__(self, outSamplerate = 48000):
        self.player = musicplayer.createPlayer()
        self.player.outSamplerate = outSamplerate
        self.player.queue = get_songs()
        self.player.peekQueue = peek_songs

    def cmdPlayPause(self,*args):
        self.player.playing = not self.player.playing

    def cmdNext(self, *args):
        self.player.nextSong()

    def setQueue(self, queue: List[Song]):
        global songs
        songs = queue