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
from threading import Lock, Condition

from .file import cache_file


class Semaphore:
    def __init__(self, init=0):
        super().__init__()
        self._cv = Condition(Lock())
        self._counter = init

    def acquire(self, val=1):
        with self._cv:
            self._cv.wait_for(lambda: self._counter >= val)
            self._counter -= val

    def release(self, val=1):
        with self._cv:
            self._counter += val
            self._cv.notify_all()


class DualPositionBytesIO(BufferedIOBase):
    """
    Buffered I/O implementation using an in-memory bytes buffer.

    Derived from the original python2 implementation:
    <https://svn.python.org/projects/python/trunk/Lib/_pyio.py>
    """

    def __init__(self, initial_bytes=None):
        super().__init__()
        buf = bytearray()
        if initial_bytes is not None:
            buf.extend(initial_bytes)
        self._buffer = buf
        self._pos = 0
        self._write_pos = 0
        self._sem = Semaphore()

    def __getstate__(self):
        return self.__dict__.copy()

    def getvalue(self):
        """Return the bytes value (contents) of the buffer
        """
        return bytes(self._buffer)

    def read(self, n=None):
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
        self._sem.acquire(newpos - self._pos)
        buff = self._buffer[self._pos: newpos]
        self._pos = newpos
        return bytes(buff)

    def write(self, b):
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
        self._sem.release(n)
        return n

    def seek(self, pos, whence=0):
        try:
            pos.__index__
        except AttributeError:
            raise TypeError("an integer is required")
        if whence == 0:
            if pos < 0:
                raise ValueError("negative seek position %r" % (pos,))
            newpos = pos
        elif whence == 1:
            newpos = max(0, self._pos + pos)
        elif whence == 2:
            newpos = max(0, len(self._buffer) + pos)
        else:
            raise ValueError("invalid whence value")
        move = newpos - self._pos
        if move > 0:
            self._sem.acquire(move)
        elif move < 0:
            self._sem.release(-move)
        self._pos = newpos
        return self._pos

    def tell(self):
        return self._pos

    def readable(self):
        return True

    def writable(self):
        return True

    def seekable(self):
        return True


def ensure_buffered():
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if self.buff is None:
                self.buff = DualPositionBytesIO()
                self.app.download_stream(self)
            return func(self, *args, **kwargs)
        return wrapper

    return decorator


class Song:
    """Song object.

    Parameters
    ----------
    raw : dict
        Raw data from the api.
    """

    def __init__(self, raw, app):
        self.app = app
        self.id = raw['Id']
        self.name = raw['Name']
        self.album = raw['Album']
        self.artist = raw['AlbumArtist']
        self.buff = None
        self.url = cache_file(f'{self.get_id()} - {self.name}')
        self.item = None

    def __eq__(self, other):
        return self.id == other.id

    def get_id(self):
        """Returns the id."""
        return self.id

    @ensure_buffered()
    def get_input(self):
        """Returns the input of the buffer."""
        return self.buff

    def read_from_cache(self) -> bool:
        """Try to load the file from cache.

        Returns
        -------
        bool
            False if it failed.
        """
        if path.exists(self.url) and path.getsize(self.url) > 0:
            with open(self.url, 'rb') as f:
                self.buff.write(f.read())
                return True
        return False

    @ensure_buffered()
    def write_to_cache(self):
        """Write the content of the buffer to a cache file."""
        f = open(self.url, 'wb')
        f.write(self.buff.getvalue())
        f.close()

    @ensure_buffered()
    def readPacket(self, bufSize):
        """Read bytes from the buffer."""
        s = self.buff.read(bufSize)
        # print "readPacket", self, bufSize, len(s)
        return s

    @ensure_buffered()
    def seekRaw(self, offset, whence):
        """Seek the buffer."""
        self.buff.seek(offset, whence)
        # print "seekRaw", self, offset, whence, r, self.rstream.tell()
        return self.buff.tell()


class Album:
    """Album object.

    Parameters
    ----------
    raw : dict
        Raw data from the api.
    """

    def __init__(self, raw: dict):
        self.id = raw['Id']
        self.name = raw['Name']

    def get_id(self):
        """Returns the id."""
        return self.id
