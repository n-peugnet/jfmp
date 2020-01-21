class Song:
    def __init__(self, raw):
        self.url = fn
        self.f = open(fn, "rb")

    def __eq__(self, other):
        return self.url == other.url

    def readPacket(self, bufSize):
        s = self.f.read(bufSize)
        # print "readPacket", self, bufSize, len(s)
        return s

    def seekRaw(self, offset, whence):
        r = self.f.seek(offset, whence)
        # print "seekRaw", self, offset, whence, r, self.f.tell()
        return self.f.tell()

class Album:
    def __init__(self, raw):
        self.raw = raw