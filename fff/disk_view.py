class DiskView(object):
    def __init__(self, disk, begin, size):
        assert not isinstance(disk, DiskView)

        self.disk = disk
        self.begin = begin
        self.end = begin + size

        assert self.begin <= self.end

    @property
    def size(self):
        return self.end - self.begin

    def seek(self, offset):
        location = self.begin + offset

        assert location >= self.begin and location < self.end
        self.disk.seek(location)

    def read(self, size, offset=None):
        if offset is not None:
            self.seek(offset)
        assert self.disk.tell() + size - 1 < self.end
        return self.disk.read(size)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '<DiskView {} {}>'.format(self.begin, self.size)
