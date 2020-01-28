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

from typing import List

from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from .constants import CLIENT_NAME
from .data import Song, Album
from .interfaces import AppInterface


class QueueQListWidget(QListWidget):
    def __init__(self, app: AppInterface, tabs: QTabWidget, parent=None):
        super().__init__(parent=parent)
        self.app = app
        self.tabs = tabs
        self.doubleClicked.connect(self.on_doubleclick)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key_Return:
            self.on_doubleclick(self.indexFromItem(self.selectedItems()[0]))
        else:
            super().keyPressEvent(event)

    def on_doubleclick(self, item: QListWidgetItem, **kwargs):
        """Handler for double click event on album."""
        self.app.player.play_queue_song(item.row())


class AlbumQListWidget(QListWidget):
    def __init__(self,
                 app: AppInterface,
                 tabs: QTabWidget,
                 queue: QueueQListWidget,
                 parent=None):
        super().__init__(parent=parent)
        self.app = app
        self.tabs = tabs
        self.queue = queue
        self.doubleClicked.connect(self.on_doubleclick)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key_Return:
            self.on_doubleclick(self.selectedItems()[0])
        else:
            super().keyPressEvent(event)

    def addAlbums(self, albums: List[Album]):
        """Displays a list of albums."""
        for album in albums:
            item = QListWidgetItem(album.name)
            item.setData(Qt.UserRole, album)
            self.addItem(item)

    def on_doubleclick(self, item: QListWidgetItem):
        """Handler for double click event on album."""
        album = item.data(Qt.UserRole)
        songs = self.app.client.get_album_songs(album)
        for i in range(self.queue.count()):
            self.queue.item(i).data(Qt.UserRole).item = None
        self.queue.clear()
        for song in songs:
            item = QListWidgetItem(song.name)
            item.setData(Qt.UserRole, song)
            song.item = item
            self.queue.addItem(item)
        self.tabs.setCurrentWidget(self.queue)
        self.app.play_songs(songs)


class PlayerWindow(QMainWindow):
    """Main playback window.

    Parameters
    ----------
    app : AppInterface
        The main app object.
    parent : QtWidget, optional
        The parent widget, by default None
    """

    def __init__(self, app: AppInterface, parent=None):
        super(PlayerWindow, self).__init__(parent=parent)
        self.app = app
        self.setWindowTitle(CLIENT_NAME)

        self.list_tabs = QTabWidget()
        self.queue_list = QueueQListWidget(app, self.list_tabs)
        self.queue_list.setFrameStyle(QFrame.NoFrame)
        self.albums_list = AlbumQListWidget(
            app, self.list_tabs, self.queue_list)
        self.albums_list.setFrameStyle(QFrame.NoFrame)
        self.list_tabs.addTab(self.albums_list, 'Albums')
        self.list_tabs.addTab(self.queue_list, 'Queue')
        self.list_tabs.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.MinimumExpanding)
        self.list_tabs.setStyleSheet(
            "QListView::item { height: 17px; width: 100%}")
        self.song_label = QLabel()
        self.song_label.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Ignored)
        self.song_label.setFrameShape(QFrame.StyledPanel)
        palette = self.song_label.palette()
        palette.setColor(self.song_label.backgroundRole(), Qt.white)
        self.song_label.setAutoFillBackground(True)
        self.song_label.setPalette(palette)
        self.button_play = QPushButton()
        self.button_play.setIcon(QIcon.fromTheme('media-playback-start'))
        self.button_play.setMaximumWidth(30)
        self.button_play.clicked.connect(app.player.cmd_play_pause)
        self.button_next = QPushButton()
        self.button_next.setIcon(QIcon.fromTheme('media-skip-forward'))
        self.button_next.setMaximumWidth(30)
        self.button_next.clicked.connect(app.player.cmd_next)

        app.player.add_event_listener('song_change', self.on_song_change)
        app.player.add_event_listener('playing_change', self.on_playing_change)

        controls = QWidget()
        controls_layout = QHBoxLayout()
        layout = QVBoxLayout()
        layout.addWidget(self.list_tabs)
        layout.addWidget(controls)
        controls_layout.addWidget(self.button_play)
        controls_layout.addWidget(self.button_next)
        controls_layout.addWidget(self.song_label)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        content = QWidget()
        content.setLayout(layout)
        controls.setLayout(controls_layout)
        # Set dialog layout
        self.setCentralWidget(content)

        # Add Shortcuts
        QShortcut(
            QKeySequence(Qt.Key_Space),
            content,
            app.player.cmd_play_pause)
        QShortcut(
            QKeySequence(Qt.Key_Right),
            content,
            app.player.cmd_next)

    # pylint: disable=unused-argument
    def on_song_change(self, oldSong: Song, newSong: Song, **kwargs):
        """Handler for song change event."""
        label = f'{newSong.name} - {newSong.album} - {newSong.artist}'
        self.song_label.setText(label)
        self.song_label.setToolTip(label)
        if oldSong is not None and oldSong.item is not None:
            oldSong.item.setIcon(QIcon())
        newSong.item.setIcon(QIcon.fromTheme('media-playback-start'))

    def display_albums(self, albums: List[Album]):
        """Displays a list of albums."""
        self.albums_list.addAlbums(albums)

    def on_playing_change(self, playing: bool):
        """Handler for playing change event."""
        if playing:
            self.button_play.setIcon(QIcon.fromTheme('media-playback-pause'))
        else:
            self.button_play.setIcon(QIcon.fromTheme('media-playback-start'))


class LoginDialog(QDialog):
    """Login dialog.

    Parameters
    ----------
    app : AppInterface
        The main app object
    parent : QtWidget, optional
        The parent widget, by default None
    """

    def __init__(self, app: AppInterface, parent=None):
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
        if not self.app.client.log_in(
            self.host.text(),
            self.username.text(),
            self.password.text()
        ):
            LoginDialog(self.app, self.parentWidget()).show()
        else:
            self.app.display_latest_albums()
