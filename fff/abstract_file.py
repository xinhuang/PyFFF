from abc import ABC, abstractmethod, abstractproperty
from typing import Iterable


class AbstractFile(ABC):
    @abstractproperty
    def size(self) -> int:
        pass

    @abstractproperty
    def allocated_size(self) -> int:
        pass

    @abstractproperty
    def data(self) -> bytes:
        pass

    @abstractproperty
    def mime(self) -> str:
        pass

    @abstractproperty
    def name(self) -> str:
        pass

    @abstractproperty
    def fullpath(self) -> str:
        pass

    @abstractproperty
    def parent(self) -> 'AbstractFile':
        pass

    @abstractmethod
    def read(self, count: int, skip: int, bsize: int) -> Iterable[bytes]:
        pass
