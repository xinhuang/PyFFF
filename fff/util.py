from .abstract_file import AbstractFile

from hexdump import hexdump
import hashlib
import collections

hd = hexdump


def md5sum(data):
    if isinstance(data, bytes):
        return hashlib.md5(data).hexdigest()
    elif isinstance(data, collections.Iterable):
        return md5sum(b''.join(data))
    elif isinstance(data, AbstractFile):
        return md5sum(data.data)
