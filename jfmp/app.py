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

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import Slot, QRunnable, QThreadPool, Qt

from .constants import CLIENT_NAME
from .data import Song, Album
from .client import Client
from .player import Player


def main():
    """Main program."""
    app = App()
    app.run()


class App:
    """App class

    Main object that contains everything else.
    """

    def __init__(self):
        # Create our Music Player.
        self.player = Player()
        # Create our Jellyfin Client.
        self.client = Client()
        self.threadpool = QThreadPool()
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
            self.threadpool.start(worker)

    def play_songs(self, songs: List[Song]):
        """Replaces the queue with the given album songs and start playing.

        Parameters
        ----------
        album : Album
            The album to start playing.
        """
        worker = Worker(
            lambda songs: [self.download_stream(s) for s in songs], songs)
        self.threadpool.start(worker)
        sleep(2)  # dirty sleep before I find a way to wait for the stream loading
        self.player.set_queue(songs)
        self.player.cmd_play()
        return songs

    def download_stream(self, song: Song):
        """Fills the buffer of a given song."""
        if not song.read_from_cache():
            self.client.get_audio_stream(song)
            song.write_to_cache()


class PlayerWindow(QMainWindow):
    """Main playback window.

    Parameters
    ----------
    app : App
        The main app object.
    parent : QtWidget, optional
        The parent widget, by default None
    """

    def __init__(self, app: App, parent=None):
        super(PlayerWindow, self).__init__(parent=parent)
        self.app = app
        self.setWindowTitle(CLIENT_NAME)

        self.albums_list = QListWidget()
        self.queue_list = QListWidget()
        self.albums_list.setStyleSheet("QListView::item { height: 17px; width: 100%}")
        self.queue_list.setStyleSheet("QListView::item { height: 17px; width: 100%}")
        self.list_tabs = QTabWidget()
        self.list_tabs.addTab(self.albums_list, 'Albums')
        self.list_tabs.addTab(self.queue_list, 'Queue')
        self.song_label = QLabel('None')
        self.album_label = QLabel('None')
        self.artist_label = QLabel('None')
        self.button_play = QPushButton('Play/Pause')
        self.button_next = QPushButton('Next')
        self.button_play.clicked.connect(app.player.cmd_play_pause)
        self.button_next.clicked.connect(app.player.cmd_next)

        self.albums_list.doubleClicked.connect(self.on_album_doubleclick)
        app.player.add_event_listener('song_change', self.on_song_change)

        layout = QVBoxLayout()
        layout.addWidget(self.list_tabs)
        layout.addWidget(self.song_label)
        layout.addWidget(self.album_label)
        layout.addWidget(self.artist_label)
        layout.addWidget(self.button_play)
        layout.addWidget(self.button_next)
        content = QWidget()
        content.setLayout(layout)
        # Set dialog layout
        self.setCentralWidget(content)

    # pylint: disable=unused-argument
    def on_song_change(self, oldSong: Song, newSong: Song, **kwargs):
        """Handler for song change event."""
        self.song_label.setText(newSong.Name)
        self.album_label.setText(newSong.Album)
        self.artist_label.setText(newSong.AlbumArtist)
        if oldSong is not None and oldSong.item is not None:
            oldSong.item.setIcon(QIcon())
        newSong.item.setIcon(QIcon.fromTheme('media-playback-start'))

    def display_albums(self, albums: List[Album]):
        """Displays a list of albums."""
        for album in albums:
            item = QListWidgetItem(album.Name)
            item.setData(Qt.UserRole, album)
            self.albums_list.addItem(item)

    def on_album_doubleclick(self, item: QListWidgetItem):
        """Handler for double click event on album."""
        album = item.data(Qt.UserRole)
        songs = self.app.client.get_album_songs(album)
        for i in range(self.queue_list.count()):
            self.queue_list.item(i).data(Qt.UserRole).item = None
        self.queue_list.clear()
        for song in songs:
            item = QListWidgetItem(song.Name)
            item.setData(Qt.UserRole, song)
            song.item = item
            self.queue_list.addItem(item)
        self.list_tabs.setCurrentWidget(self.queue_list)
        self.app.play_songs(songs)


class LoginDialog(QDialog):
    """Login dialog.

    Parameters
    ----------
    app : App
        The main app object
    parent : QtWidget, optional
        The parent widget, by default None
    """

    def __init__(self, app: App, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.app = app
        self.setWindowTitle(CLIENT_NAME)

        self.host_label = QLabel('Host')
        self.host = QLineEdit('https://jellyfin.org')
        self.username_label = QLabel('Username')
        self.username = QLineEdit('')
        self.password_label = QLabel('Password')
        self.password = QLineEdit('')
        self.password.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Log in")
        self.login_button.clicked.connect(self.login)

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.host_label)
        layout.addWidget(self.host)
        layout.addWidget(self.username_label)
        layout.addWidget(self.username)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password)
        layout.addWidget(self.login_button)
        # Set dialog layout
        self.setLayout(layout)

    @Slot()
    def login(self):
        """Try to log in"""
        self.destroy()
        if not self.app.client.log_in(self.host.text(), self.username.text(), self.password.text()):
            LoginDialog(self.app, self.parentWidget()).show()
        else:
            self.app.display_latest_albums()


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
