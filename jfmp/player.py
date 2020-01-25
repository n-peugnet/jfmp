# Copyright (C) 2020  Nicolas Peugnet
#
# This file is part of jfmp.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pprint
from collections import defaultdict
from typing import List

import musicplayer

from .data import Song, clone_song

# FFmpeg log levels: {0:panic, 8:fatal, 16:error, 24:warning, 32:info, 40:verbose}
musicplayer.setFfmpegLogLevel(20)

class Player():
    def __init__(self, outSamplerate = 48000):
        self.core = musicplayer.createPlayer()
        self.core.outSamplerate = outSamplerate
        self.core.queue = self.get_songs()
        self.core.peekQueue = self.peek_songs
        self.core.onSongChange = self._process_onSongChange
        self.songs = []
        self.curr_song = 0
        self.events = defaultdict(list)

    def get_songs(self):
        while True:
            yield self.songs[self.curr_song]
            self.curr_song += 1
            if self.curr_song >= len(self.songs):
                self.curr_song = 0

    def peek_songs(self, n):
        next_song = self.curr_song + 1
        if next_song >= len(self.songs):
            next_song = 0
        return map(clone_song, (self.songs[next_song:] + self.songs[:next_song])[:n])

    def cmd_play(self):
        self.core.playing = True

    def cmd_pause(self):
        self.core.playing = False

    def cmd_play_pause(self,*args):
        if not self.core.playing and len(self.songs) == 0:
            return False
        self.core.playing = not self.core.playing

    def cmd_next(self, *args):
        self.core.nextSong()

    def get_metadata(self):
        return pprint.pformat(self.core.curSongMetadata)

    def set_queue(self, songs: List[Song]):
        self.songs = songs
        self.curr_song = -1
        self.core.nextSong()

    def add_to_queue(self, song: Song):
        self.songs += song

    def add_event_listener(self, event: str, func):
        self.events[event].append(func)

    def _process_events(self, event: str, **kwargs):
        if self.events.get(event):
            for func in self.events[event]:
                func(**kwargs)

    def _process_onSongChange(self, **kwargs):
        self._process_events('song_change', **kwargs)