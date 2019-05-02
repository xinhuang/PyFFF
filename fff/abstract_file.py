from abc import ABC, abstractmethod, abstractproperty
from typing import Iterable


class AbstractFile(ABC):
    """
    This is the generic File interface.
    """

    @abstractproperty
    def size(self) -> int:
        """int: The actual size of this file on disk. Abstract property.
        """
        pass

    @abstractproperty
    def allocated_size(self) -> int:
        """int: The allocated size of this file on disk. Abstract property.
        """
        pass

    @abstractproperty
    def data(self) -> bytes:
        """bytes: The data of this file in bytes. Abstract property.
        """
        pass

    @abstractproperty
    def mime(self) -> str:
        """str: The mime type of this file. E.g. "application/x-gzip". Abstract property.
        """
        pass

    @abstractproperty
    def name(self) -> str:
        """str: The name of this file.
        Abstract property.
        """
        pass

    @abstractproperty
    def fullpath(self) -> str:
        """str: The full path of this file. E.g. "/usr/local/bin/python".
        Abstract property.

        Note
        -----
        For root directory, it returns "/".
        """
        pass

    @abstractproperty
    def parent(self) -> 'AbstractFile':
        """AbstractFile: The parent directory of this file.
        Abstract property.
        """
        pass

    @abstractmethod
    def read(self, count: int, skip: int, bsize: int) -> Iterable[bytes]:
        """Read file data at given location.
        Abstract method.

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
            The result is a generate of bytes.

        Examples
        --------
        Read the 2nd cluster of the file.

        >>> f.read(count=1, skip=1, bsize=fs.cluster_size)
        b'This is the data contained in the second cluster of this file... [truncated]'
        """
        pass
