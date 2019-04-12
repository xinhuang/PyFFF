from . import data_units as du

from typing import Optional


class DiskView(object):
    def __init__(self, disk, begin: int, size: int,
                 sector_size: Optional[int] = None, cluster_size: Optional[int] = None):
        assert not isinstance(disk, DiskView)

        self.disk = disk
        self.begin = begin
        self.end = begin + size

        assert self.begin <= self.end
        assert sector_size is None or sector_size > 0
        assert cluster_size is None or cluster_size > 0

        if sector_size is not None:
            self.sector_size = sector_size
            self.sectors = du.DataUnits(self, sector_size, self.size // sector_size)
        if cluster_size is not None:
            self.cluster_size = cluster_size
            self.clusters = du.DataUnits(self, cluster_size, self.size // cluster_size)

    @property
    def size(self):
        return self.end - self.begin

    def _seek(self, offset):
        location = self.begin + offset

        assert location >= self.begin and location < self.end
        self.disk.seek(location)

    def read(self, size, offset=None):
        if offset is not None:
            self._seek(offset)
        assert self.disk.tell() + size - 1 < self.end
        return self.disk.read(size)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '<DiskView {} {}>'.format(self.begin, self.size)
