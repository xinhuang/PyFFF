from .disk_view import DiskView


class Entity(object):
    def __init__(self, disk, sector_offset, last_sector, sector_size, number, parent):
        self.begin = sector_offset * sector_size
        self.end = (last_sector + 1) * sector_size
        self.size = self.end - self.begin
        self.dv = DiskView(disk, self.begin, self.size)
        self.sector_offset = sector_offset
        self.last_sector = last_sector
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
