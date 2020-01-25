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

from os import path
from io import BufferedIOBase

from .file import cache_file


class DualPositionBytesIO(BufferedIOBase):

    """
    Buffered I/O implementation using an in-memory bytes buffer.

    Derived from the original python2 implementation:
    <https://svn.python.org/projects/python/trunk/Lib/_pyio.py>
    """

    def __init__(self, initial_bytes=None):
        buf = bytearray()
        if initial_bytes is not None:
            buf.extend(initial_bytes)
        self._buffer = buf
        self._pos = 0
        self._write_pos = 0

    def __getstate__(self):
        if self.closed:
            raise ValueError("__getstate__ on closed file")
        return self.__dict__.copy()

    def getvalue(self):
        """Return the bytes value (contents) of the buffer
        """
        if self.closed:
            raise ValueError("getvalue on closed file")
        return bytes(self._buffer)

    def read(self, n=None):
        if self.closed:
            raise ValueError("read from closed file")
        if n is None:
            n = -1
        if not isinstance(n, int):
            raise TypeError("integer argument expected, got {0!r}".format(
                type(n)))
        if n < 0:
            n = len(self._buffer)
        if len(self._buffer) <= self._pos:
            return b""
        newpos = min(len(self._buffer), self._pos + n)
        b = self._buffer[self._pos : newpos]
        self._pos = newpos
        return bytes(b)

    def read1(self, n):
        """This is the same as read.
        """
        return self.read(n)

    def write(self, b):
        if self.closed:
            raise ValueError("write to closed file")
        if isinstance(b, str):
            raise TypeError("can't write unicode to binary stream")
        n = len(b)
        if n == 0:
            return 0
        pos = self._write_pos
        if pos > len(self._buffer):
            # Inserts null bytes between the current end of the file
            # and the new write position.
            padding = b'\x00' * (pos - len(self._buffer))
            self._buffer += padding
        self._buffer[pos:pos + n] = b
        self._write_pos += n
        return n

    def seek(self, pos, whence=0):
        if self.closed:
            raise ValueError("seek on closed file")
        try:
            pos.__index__
        except AttributeError:
            raise TypeError("an integer is required")
        if whence == 0:
            if pos < 0:
                raise ValueError("negative seek position %r" % (pos,))
            self._pos = pos
        elif whence == 1:
            self._pos = max(0, self._pos + pos)
        elif whence == 2:
            self._pos = max(0, len(self._buffer) + pos)
        else:
            raise ValueError("invalid whence value")
        return self._pos

    def tell(self):
        if self.closed:
            raise ValueError("tell on closed file")
        return self._pos

    def truncate(self, pos=None):
        if self.closed:
            raise ValueError("truncate on closed file")
        if pos is None:
            pos = self._pos
        else:
            try:
                pos.__index__
            except AttributeError:
                raise TypeError("an integer is required")
            if pos < 0:
                raise ValueError("negative truncate position %r" % (pos,))
        del self._buffer[pos:]
        return pos

    def readable(self):
        return True

    def writable(self):
        return True

    def seekable(self):
        return True


class Song:
    def __init__(self, raw):
        self.raw = raw
        self.id = raw['Id']
        self.Name = raw['Name']
        self.Album = raw['Album']
        self.AlbumArtist = raw['AlbumArtist']
        self.buff = DualPositionBytesIO()
        self.url = cache_file(f'{self.get_id()} - {self.Name}')

    def __eq__(self, other):
        return self.id == other.id

    # def __getattr__(self, name):
    #     return self.raw.get(name)

    def get_id(self):
        return self.id

    def get_input(self):
        return self.buff

    def read_from_cache(self):
        if path.exists(self.url) and path.getsize(self.url) > 0:
            with open(self.url, 'rb') as f:
                self.buff.write(f.read())
                return True
        return False

    def write_to_cache(self):
        f = open(self.url, 'wb')
        f.write(self.buff.getvalue())
        f.close()

    def readPacket(self, bufSize):
        s = self.buff.read(bufSize)
        # print "readPacket", self, bufSize, len(s)
        return s

    def seekRaw(self, offset, whence):
        r = self.buff.seek(offset, whence)
        # print "seekRaw", self, offset, whence, r, self.rstream.tell()
        return self.buff.tell()

    def clone(self):
        return Song(self.raw)


class Album:
    def __init__(self, raw: dict):
        self.raw = raw
        self.id = raw['Id']
    
    def __getattr__(self, name):
        return self.raw.get(name)

    def get_id(self):
        return self.id


def clone_song(song: Song) -> Song:
    return song.clone()
