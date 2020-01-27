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

import socket
import json
import os
from typing import List

from jellyfin_apiclient_python.client import JellyfinClient
from jellyfin_apiclient_python.connection_manager import CONNECTION_STATE

from .file import conf_file
from .constants import CLIENT_NAME, CLIENT_VERSION, COMMAND_NAME
from .data import Song, Album

CREDENTIALS_LOCATION = conf_file('cred.json')


def ensure_logged_in():
    """Unused decorator for now..."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if self.logged_in is False:
                self.connect()
            return func(self, *args, **kwargs)
        return wrapper

    return decorator


class Client(JellyfinClient):
    """JellyfinClient extension with higher level calls."""

    def __init__(self):
        super().__init__()
        self.config.data['app.default'] = True
        self.config.app(
            CLIENT_NAME,
            CLIENT_VERSION,
            socket.gethostname(),
            f'{COMMAND_NAME}@{socket.gethostname()}')
        self.config.data['http.user_agent'] = f'{COMMAND_NAME}/{CLIENT_VERSION}'
        self.config.data['auth.ssl'] = True

    def connect(self) -> bool:
        """Try to connect using the current credentials."""
        credentials = self._load_credentials()
        if credentials is None:
            return False
        state = self.authenticate(credentials)
        if state['State'] != CONNECTION_STATE['SignedIn']:
            return False
        # self.callback = event
        # self.callback_ws = event
        self.start(websocket=True)
        return True

    def log_in(self, host: str, username: str, password: str) -> bool:
        """Try to connect using the user informations.

        Parameters
        ----------
        host : str
            The host to connect to.
        username : str
            The username.
        password : str
            The password.

        Returns
        -------
        bool
            True if it mannaged to connect, False otherwise.
        """
        if self.auth.connect_to_address(host) is False:
            return False
        if self.auth.login(host, username, password) is False:
            return False
        state = self.auth.connect()
        if state['State'] == CONNECTION_STATE['SignedIn']:
            self._save_credentials(self.auth.credentials.get_credentials())
            return self.connect()
        return False

    def _save_credentials(self, credentials):
        with open(CREDENTIALS_LOCATION, "w") as file:
            json.dump(credentials, file)

    def _load_credentials(self):
        if os.path.exists(CREDENTIALS_LOCATION):
            with open(CREDENTIALS_LOCATION) as file:
                return json.load(file)
        return None

    # @ensure_logged_in()
    def get_latest_albums(self) -> List[Album]:
        """Fetches latests albums from the api."""
        return [Album(a) for a in self.jellyfin.get_recently_added(
            'Audio',
            limit=100
        )]

    def get_album_songs(self, album: Album) -> List[Song]:
        """Fetches a given album's songs from the api."""
        response = self.jellyfin.user_items(params={
            'ParentId': album.get_id(),
            'IncludeItemTypes': 'Audio',
            'SortBy': 'SortName',
        })
        return [Song(i) for i in response['Items']]

    def get_audio_stream(self, song: Song):
        """Downloads the audio stream for a file."""
        self.jellyfin.get_audio_stream(
            song.get_input(),
            song.get_id(),
            'test',
            'opus,mp3|mp3,aac,m4a|aac,flac,webma,webm,wav')
