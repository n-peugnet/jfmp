import socket
import json
import os
from getpass import getpass
from typing import List

from .jellyfin.jellyfin_apiclient_python.client import JellyfinClient
from .jellyfin.jellyfin_apiclient_python.connection_manager import CONNECTION_STATE

from .file import conf_file
from .constants import CLIENT_NAME, CLIENT_VERSION, COMMAND_NAME
from .data import Song, Album

credentials_location = conf_file('cred.json')


def ensure_logged_in():

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if self.logged_in is False:
                self.connect()
            return func(self, *args, **kwargs)
        return wrapper

    return decorator


class Client(JellyfinClient):
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
        if self.auth.connect_to_address(host) is False: return False
        if self.auth.login(host, username, password) is False: return False
        state = self.auth.connect()
        if state['State'] == CONNECTION_STATE['SignedIn']:
            self._save_credentials(self.auth.credentials.get_credentials())
            return self.connect()
        return False

    def _save_credentials(self, credentials):
        with open(credentials_location, "w") as cf:
            json.dump(credentials, cf)

    def _load_credentials(self):
        if os.path.exists(credentials_location):
            with open(credentials_location) as cf:
                return json.load(cf)
        return None

    # @ensure_logged_in()
    def get_latest_albums(self) -> List[Album]:
        return [Album(a) for a in self.jellyfin.get_recently_added('Audio')]

    def get_album_songs(self, album: Album) -> List[Song]:
        response = self.jellyfin.user_items(params={
            'ParentId': album.get_id(),
            'IncludeItemTypes': 'Audio'
        })
        return [Song(i) for i in response['Items']]

    def get_audio_stream(self, song: Song):
        self.jellyfin.get_audio_stream(song.wstream, song.get_id(), 'test', 'opus,mp3|mp3,aac,m4a|aac,flac,webma,webm,wav')
