from .entity import Entity
from .data_units import DataUnits


class UnallocatedSpace(Entity):
    def __init__(self, sector_offset, last_sector, parent):
        Entity.__init__(self, parent.dv.disk,
                        sector_offset * parent.sector_size,
                        (last_sector - sector_offset + 1) * parent.sector_size,
                        parent.sector_size, -1, parent)
        self.sectors = DataUnits(self, self.sector_size, self.sector_count)

    def tabulate(self):
        return [[self.index,
                 '{}:-'.format(self.parent.number),
                 self.sector_offset,
                 self.last_sector,
                 self.sector_count,
                 'Unallocated',
                 '---']]

    def __str__(self):
        return tabulate(self.tabulate(),
                        headers=['#', 'Slot', 'Start', 'End', 'Length',
                                 'Description', 'CHS', ])
