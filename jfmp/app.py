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

from time import sleep
from typing import List

from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Slot, QRunnable, QThreadPool

from .client import Client
from .data import Song
from .interfaces import AppInterface
from .player import Player
from .gui import PlayerWindow, LoginDialog


def main():
    """Main program."""
    app = App(Player(96000), Client())
    app.run()


class App(AppInterface):
    """App class

    Main object that contains everything else.
    """

    def __init__(self, player: Player, client: Client):
        super().__init__(player, client)
        self._threadpool = QThreadPool()
        self.main = None

    def run(self):
        """Runs the app"""
        # Qt GUI
        app = QApplication([])
        self.main = PlayerWindow(self)

        if not self.client.connect():
            dialog = LoginDialog(self, self.main)
            dialog.show()
        else:
            self.display_latest_albums()

        self.main.show()

        # Run the main Qt loop
        app.exec_()
        self.client.stop()

    def display_latest_albums(self):
        """Fetches then displays latests albums inside the GUI."""
        def display_latest_albums():
            self.main.display_albums(self.client.get_latest_albums())
        if self.client.logged_in:
            worker = Worker(display_latest_albums)
            self._threadpool.start(worker)

    def play_songs(self, songs: List[Song]):
        """Replaces the queue with the given album songs and start playing.

        Parameters
        ----------
        album : Album
            The album to start playing.
        """
        worker = Worker(
            lambda songs: [self.download_stream(s) for s in songs], songs)
        self._threadpool.start(worker)
        sleep(2)  # dirty sleep before I find a way to wait for the stream load
        self.player.play_new_queue(songs)
        return songs

    def download_stream(self, song: Song):
        """Fills the buffer of a given song."""
        if not song.read_from_cache():
            self.client.get_audio_stream(song)
            song.write_to_cache()


class Worker(QRunnable):
    """Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    Parameters
    ----------
    func : function
        The function callback to run on this worker thread.
        Supplied args and kwargs will be passed through to the runner.

    args :
        Arguments to pass to the callback function.

    kwargs :
        Keywords to pass to the callback function.
    """

    def __init__(self, func, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        """Initialises the runner function with passed args, kwargs."""
        self.func(*self.args, **self.kwargs)
