from .disk_view import DiskView


class Entity(object):
    def __init__(self, disk, offset, size, sector_size, number, parent):
        self.begin = offset
        self.end = offset + size
        self.size = size
        self.dv = DiskView(disk, self.begin, self.size)
        assert offset % sector_size == 0
        self.sector_offset = offset // sector_size
        # FIXME: There shouldn't be slack space in the unit of sector
        self.last_sector = self.end // sector_size - 1
        self.sector_size = sector_size
        self.parent = parent
        self.index = -1 if parent else 0
        self.number = number

    @property
    def sector_count(self):
        return self.last_sector - self.sector_offset + 1

    @property
    def entities(self):
        yield self

    def read(self, offset, size=None):
        size = size if size else self.sector_size
        self.dv.seek(offset)
        return self.dv.read(size)
