from .entity import Entity
from .data_units import DataUnits


class UnallocatedSpace(Entity):
    def __init__(self, first_sector, last_sector, parent):
        Entity.__init__(self)

        sector_count = last_sector - first_sector
        self.entities = [self]
        self.parent = parent
        self.first_sector = first_sector
        self.last_sector = last_sector

        self.sectors = DataUnits(self, self.sector_size, sector_count)

    @property
    def sector_size(self):
        return self.parent.sector_size

    def tabulate(self):
        return [[self.index,
                 '{}:-'.format(self.parent.number),
                 self.first_sector,
                 self.last_sector,
                 len(self.sectors),
                 'Unallocated',
                 '---']]

    def __str__(self):
        return tabulate(self.tabulate(),
                        headers=['#', 'Slot', 'Start', 'End', 'Length',
                                 'Description', 'CHS', ])
