# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import sys
import os
import fnmatch
from pprint import pprint
from functools import partial

from PySide2.QtWidgets import *
from PySide2.QtCore import Slot, QRunnable, QThreadPool, Qt

from .constants import CLIENT_NAME
from .data import Song
from .client import Client
from .player import Player

class App(object):
    def __init__(self):
        # Create our Music Player.
        self.player = Player()
        # Create our Jellyfin Client.
        self.client = Client()
        self.threadpool = QThreadPool()

    def run(self):
        # Qt GUI
        app = QApplication([])
        main = PlayerWindow(self.threadpool, self.player, self.client)

        if not self.client.connect():
            dialog = LoginDialog(self.client, main)
            dialog.show()
        else:
            worker = Worker(main.load_latest_albums)
            self.threadpool.start(worker)

        main.show()

        # Run the main Qt loop
        app.exec_()
        self.client.stop()


class PlayerWindow(QMainWindow):
    def __init__(self, threadpool: QThreadPool, player: Player, client: Client, parent=None):
        super(PlayerWindow, self).__init__(parent=parent)
        self.threadpool = threadpool
        self.player = player
        self.client = client
        self.setWindowTitle(CLIENT_NAME)
        self.albums_list = QListWidget()
        self.song_label = QLabel('None')
        self.album_label = QLabel('None')
        self.artist_label = QLabel('None')
        self.button_play = QPushButton('Play/Pause')
        self.button_next = QPushButton('Next')
        self.button_play.clicked.connect(player.cmd_play_pause)
        self.button_next.clicked.connect(player.cmd_next)

        self.albums_list.doubleClicked.connect(self.play_album_songs)
        self.player.add_event_listener('song_change', self.on_song_change)

        layout = QVBoxLayout()
        layout.addWidget(self.albums_list)
        layout.addWidget(self.song_label)
        layout.addWidget(self.album_label)
        layout.addWidget(self.artist_label)
        layout.addWidget(self.button_play)
        layout.addWidget(self.button_next)
        content = QWidget()
        content.setLayout(layout)
        # Set dialog layout
        self.setCentralWidget(content)

    def on_song_change(self, newSong, **kwargs):
        self.song_label.setText(newSong.Name)
        self.album_label.setText(newSong.Album)
        self.artist_label.setText(newSong.AlbumArtist)

    def load_latest_albums(self):
        if self.client.logged_in:
            for album in self.client.get_latest_albums():
                item = QListWidgetItem(album.Name)
                item.setData(Qt.UserRole, album)
                self.albums_list.addItem(item)

    def play_album_songs(self, item: QListWidgetItem):
        album = item.data(Qt.UserRole)
        songs = self.client.get_album_songs(album)
        self.player.set_queue(songs)
        worker = Worker(lambda songs: [self.client.get_audio_stream(s) for s in songs], songs)
        self.threadpool.start(worker)
        self.player.core.playing = True


class LoginDialog(QDialog):
    def __init__(self, client: Client, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.client = client
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
        if not self.client.log_in(self.host.text(),self.username.text(), self.password.text()):
            print('error')
        else:
            self.destroy()

class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        self.fn(*self.args, **self.kwargs)