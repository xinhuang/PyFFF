from .abstract_file import AbstractFile

from hexdump import hexdump

import hashlib
import collections
from typing import Union, Iterable, cast


def hd(*args, **kwargs):
    """This is an alias to the `hexdump` function."""
    hexdump(*args, **kwargs)


def md5sum(data: Union[bytes, Iterable[bytes], AbstractFile]) -> str:
    """Returns the MD5 checksum of bytes, an iterable of bytes, or a file.

    Parameters
    ----------
    data : bytes, Iterable[bytes], or AbstractFile
        The data/file to calculate MD5 checksum on.

    Returns
    -------
    str
        The MD5 checksum string.
    """
    if isinstance(data, bytes):
        return hashlib.md5(data).hexdigest()
    elif isinstance(data, collections.Iterable):
        data = cast(Iterable[bytes], data)
        return md5sum(b''.join(data))
    elif isinstance(data, AbstractFile):
        return md5sum(data.data)
