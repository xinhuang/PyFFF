class DataUnits(object):
    def __init__(self, entity, unit_size, unit_count):
        self.entity = entity
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
            return self.entity.read(offset, self.unit_size)
        elif isinstance(index_or_slice, slice):
            s = index_or_slice
            begin = self._convert(s.start)
            end = self._convert(s.stop)
            n = end - begin
            return self.entity.read(begin * self.unit_size,
                                    n * self.unit_size)
