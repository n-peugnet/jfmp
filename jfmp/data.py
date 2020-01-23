from os import path

from .file import cache_file

class Song:
    def __init__(self, raw):
        self.raw = raw
        self.id = raw['Id']
        self.path = cache_file(self.get_id())
        if path.exists(self.path):
            self.wstream = open(self.path, "ab")
        else:
            self.wstream = open(self.path, "wb")
        self.rstream = open(self.path, "rb")

    def __eq__(self, other):
        return self.url == other.url

    def __getattr__(self, name):
        return self.raw.get(name)

    def get_id(self):
        return self.id

    def readPacket(self, bufSize):
        s = self.rstream.read(bufSize)
        # print "readPacket", self, bufSize, len(s)
        return s

    def seekRaw(self, offset, whence):
        r = self.rstream.seek(offset, whence)
        # print "seekRaw", self, offset, whence, r, self.rstream.tell()
        return self.rstream.tell()

    def clone(self):
        return Song(self.raw)


class Album:
    def __init__(self, raw: dict):
        self.raw = raw
        self.id = raw['Id']
    
    def __getattr__(self, name):
        return raw.get(name)

    def get_id(self):
        return self.id


def clone_song(song: Song) -> Song:
    return song.clone()
