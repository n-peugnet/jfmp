import socket
import json
import os
from getpass import getpass

from jellyfin_apiclient_python import Jellyfin
from jellyfin_apiclient_python.connection_manager import CONNECTION_STATE

from jfmp import conffile
from jfmp.constants import CLIENT_NAME, CLIENT_VERSION, COMMAND_NAME

credentials_location = conffile.get(COMMAND_NAME,'cred.json')

class Client(object):
    def __init__(self):
        conn = Jellyfin(None)
        conn.config.data['app.default'] = True
        conn.config.app(CLIENT_NAME, CLIENT_VERSION, socket.gethostname(), f'{COMMAND_NAME}@{socket.gethostname()}')
        conn.config.data['http.user_agent'] = f'{COMMAND_NAME}/{CLIENT_VERSION}'
        conn.config.data['auth.ssl'] = True

        self.conn = conn
        self.credentials = None

    def connect(self):
        is_logged_in = False
        if not self.load_credentials():
            while not is_logged_in:
                host = input("Server URL: ")
                username = input("Username: ")
                password = getpass("Password: ")
                self.conn.auth.connect_to_address(host)
                self.conn.auth.login(host, username, password)
                state = self.conn.auth.connect()
                is_logged_in = state['State'] == CONNECTION_STATE['SignedIn']
                if is_logged_in:
                    credentials = self.conn.auth.credentials.get_credentials()
                    with open(credentials_location, "w") as cf:
                        json.dump(credentials, cf)
                    self.conn.authenticate(credentials)
        else:
            state = self.conn.authenticate(self.credentials)
            if state['State'] == CONNECTION_STATE['SignedIn']:
                is_logged_in = True

        def event(event_name, data):
            self.callback(conn, event_name, data)

        self.conn.callback = event
        self.conn.callback_ws = event
        self.conn.start(websocket=True)

        print(self.conn.jellyfin.get_user())
        return is_logged_in

    def close(self):
        self.conn.close()

    def save_credentials(self):
        with open(credentials_location, "w") as cf:
            json.dump(self.credentials, cf)

    def load_credentials(self):
        if os.path.exists(credentials_location):
            with open(credentials_location) as cf:
                self.credentials = json.load(cf)
            return True
        return False