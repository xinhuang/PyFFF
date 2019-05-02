from abc import ABC, abstractmethod, abstractproperty
from typing import Iterable


class AbstractFile(ABC):
    @abstractproperty
    def size(self) -> int:
        """int: The actual size of this file on disk.
        """
        pass

    @abstractproperty
    def allocated_size(self) -> int:
        """int: The allocated size of this file on disk.
        """
        pass

    @abstractproperty
    def data(self) -> bytes:
        """bytes: The data of this file in bytes.
        """
        pass

    @abstractproperty
    def mime(self) -> str:
        """str: The mime type of this file. E.g. "application/x-gzip"."""
        pass

    @abstractproperty
    def name(self) -> str:
        """str: The name of this file."""
        pass

    @abstractproperty
    def fullpath(self) -> str:
        """str: The full path of this file. 


        Note
        -----
        For example, "/usr/local/bin/python".
        For root directory, it returns "/".
        """
        pass

    @abstractproperty
    def parent(self) -> 'AbstractFile':
        """Returns the parent directory of this file."""
        pass

    @abstractmethod
    def read(self, count: int, skip: int, bsize: int) -> Iterable[bytes]:
        """Read file data at given location.

        Parameters
        ----------
        count : int
            The number of data unit to read.
        skip : int
            The number of data unit to skip before read.
        bsize : int
            The size of data unit. (Block size)

        Returns
        -------
        Iterable[bytes]
            The result is a generate of bytes."""
        pass
