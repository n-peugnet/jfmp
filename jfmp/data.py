from .file import cache_file

class Song:
    def __init__(self, raw):
        self.raw = raw
        self.id = raw['Id']
        self.f = open(cache_file(self.get_id()), "w+b")

    def __eq__(self, other):
        return self.url == other.url

    def __getattr__(self, name):
        return raw.get(name)

    def get_id(self):
        return self.id

    def readPacket(self, bufSize):
        s = self.f.read(bufSize)
        # print "readPacket", self, bufSize, len(s)
        return s

    def seekRaw(self, offset, whence):
        r = self.f.seek(offset, whence)
        # print "seekRaw", self, offset, whence, r, self.f.tell()
        return self.f.tell()

class Album:
    def __init__(self, raw: dict):
        self.raw = raw
        self.id = raw['Id']
    
    def __getattr__(self, name):
        return raw.get(name)

    def get_id(self):
        return self.id
