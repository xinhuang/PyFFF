class DiskView(object):
    def __init__(self, disk, begin, size):
        assert not isinstance(disk, DiskView)

        self.disk = disk
        self._begin = begin
        self._end = begin + size

        assert self._begin <= self._end

    @property
    def size(self):
        return self._end - self._begin

    def seek(self, offset):
        location = self._begin + offset

        assert location >= self._begin and location < self._end
        self.disk.seek(location)

    def read(self, size):
        assert self.disk.tell() + size - 1 < self._end
        return self.disk.read(size)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '<DiskView {} {}>'.format(self._begin, self.size)
