from .disk_view import DiskView
from .data_units import DataUnits

from typing import Optional


class Entity(object):
    def __init__(self, **kwargs):
        if 'filesystem' in kwargs:
            filesystem: Entity = kwargs.get('filesystem')

            self.dv: DiskView = DiskView
        else:
            self._old_init(**kwargs)

    def _old_init(self, disk, offset, size, sector_size, number, parent):
        self.begin: int = offset
        self.end: int = offset + size
        self.size: int = size
        self.dv: DiskView = DiskView(disk, self.begin, self.size)
        assert offset % sector_size == 0
        self.sector_offset: int = offset // sector_size
        # FIXME: There shouldn't be slack space in the unit of sector
        self.last_sector: int = self.end // sector_size - 1
        self.sector_size: int = sector_size
        self.parent = parent
        self.index: int = -1 if parent else 0
        self.number: int = number

        self.data: DataUnits = DataUnits(self, 1, size)
        self.sectors: DataUnits = DataUnits(self, self.sector_size, size // sector_size)

    @property
    def sector_count(self) -> int:
        return self.last_sector - self.sector_offset + 1

    @property
    def entities(self):
        yield self

    def read(self, offset: int, size: Optional[int] = None) -> bytes:
        size = size if size else self.sector_size
        self.dv.seek(offset)
        return self.dv.read(size)
