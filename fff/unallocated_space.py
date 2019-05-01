from .entity import Entity
from .data_units import DataUnits
from .disk_view import DiskView


class UnallocatedSpace(Entity):
    def __init__(self, first_sector, last_sector, parent):
        Entity.__init__(self)

        sector_count = last_sector - first_sector
        self.entities = [self]
        self.parent = parent
        self.first_sector = first_sector
        self.last_sector = last_sector
        self.dv = DiskView(parent.dv.disk, begin=self.first_sector*self.sector_size,
                           size=sector_count*self.sector_size,
                           sector_size=self.sector_size)

        self.sectors = self.dv.sectors

    @property
    def sector_size(self):
        return self.parent.sector_size

    def get_file(*args, **kwargs):
        pass

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
