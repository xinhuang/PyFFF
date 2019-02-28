from .entity import Entity


class UnallocatedSpace(Entity):
    def __init__(self, sector_offset, last_sector, parent):
        Entity.__init__(self, parent.dv.disk,
                        sector_offset * parent.sector_size,
                        (last_sector - sector_offset + 1) * parent.sector_size,
                        parent.sector_size, -1, parent)

    def tabulate(self):
        return [[self.index,
                 '{}:-'.format(self.parent.number),
                 self.sector_offset,
                 self.last_sector,
                 self.sector_count,
                 'Unallocated',
                 '---']]

    @property
    def sectors(self):
        class SectorContainer(object):
            def __init__(self, entity):
                self.entity = entity

            def _convert(self, index):
                if index >= 0:
                    return index
                else:
                    return self.entity.sector_count + index + 1

            def __getitem__(self, index_or_slice):
                sector_size = self.entity.sector_size
                if isinstance(index_or_slice, int):
                    index = self._convert(index_or_slice)
                    return self.entity.read(index, sector_size)
                elif isinstance(index_or_slice, slice):
                    s = index_or_slice
                    begin = self._convert(s.start)
                    end = self._convert(s.stop)
                    n = end - begin
                    return self.entity.read(begin * sector_size,
                                            n * sector_size)
        return SectorContainer(self)

    def __str__(self):
        return tabulate(self.tabulate(),
                        headers=['#', 'Slot', 'Start', 'End', 'Length',
                                 'Description', 'CHS', ])
