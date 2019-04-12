from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .disk_view import DiskView


class DataUnits(object):
    def __init__(self, dv: 'DiskView', unit_size: int, unit_count: int):
        self.dv = dv
        self.unit_size = unit_size
        self.unit_count = unit_count

    def _convert(self, index):
        if index >= 0:
            return index
        else:
            return self.unit_count + index

    def __getitem__(self, index_or_slice):
        if isinstance(index_or_slice, int):
            offset = self._convert(index_or_slice) * self.unit_size
            return self.dv.read(offset=offset, size=self.unit_size)
        elif isinstance(index_or_slice, slice):
            s = index_or_slice
            begin = self._convert(s.start)
            end = self._convert(s.stop)
            n = end - begin
            return self.dv.read(offset=begin * self.unit_size,
                                size=n * self.unit_size)

    def __len__(self):
        return self.unit_count
