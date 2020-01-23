# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import sys
import os
import fnmatch
import pprint
from functools import partial

from PySide2.QtWidgets import QApplication, QMainWindow, QLabel, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget
from PySide2.QtQuick import QQuickView
from PySide2.QtCore import QUrl, Slot

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

    def run(self):
        # Qt GUI
        app = QApplication([])
        view = PlayerView(self.player)

        if not self.client.connect():
            dialog = LoginDialog(self.client, view)
            dialog.show()
        else:
            albums = self.client.get_latest_albums()
            songs = self.client.get_album_songs(albums[2])
            for song in songs:
                self.client.get_audio_stream(song)

            self.player.set_queue(songs)

        view.show()

        # Run the main Qt loop
        app.exec_()
        self.client.stop()


class PlayerView(QMainWindow):
    def __init__(self, player: Player, parent=None):
        super(PlayerView, self).__init__(parent=parent)
        self.player = player
        self.setWindowTitle(CLIENT_NAME)
        self.label = QLabel('None')
        self.button_play = QPushButton('Play/Pause')
        self.button_next = QPushButton('Next')
        self.button_play.clicked.connect(player.cmd_play_pause)
        self.button_next.clicked.connect(player.cmd_next)

        self.player.onSongChange = self.onSongChange

        layout = QVBoxLayout()
        layout.addWidget(self.button_play)
        layout.addWidget(self.button_next)
        content = QWidget()
        content.setLayout(layout)
        # Set dialog layout
        self.setCentralWidget(content)

    def onSongChange(self, **kwargs):
        self.label.setText(self.player.get_metadata())


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
