from .mft_entry import MFTEntry
from .boot_sector import BootSector


from ..entity import Entity
from ..data_units import DataUnits

import struct
from tabulate import tabulate


class File(object):
    pass


class MFT(File):
    pass


class NTFS(Entity):
    def __init__(self, dv, sector0, parent):
        self.boot_sector = BootSector(sector0)

        Entity.__init__(self, dv.disk, dv.begin, dv.size,
                        self.boot_sector.bytes_per_sector,
                        -1, parent)

        self.fs_type = 'NTFS'
        self.sectors = DataUnits(self, self.sector_size, self.sector_count)

        bs = self.boot_sector
        cluster_size = self.sector_size * bs.sectors_per_cluster
        cluster_count = bs.total_sectors // bs.sectors_per_cluster
        self.clusters = DataUnits(self, cluster_size, cluster_count)

        self.mft = MFTEntry(self.clusters[self.boot_sector.mft_cluster_number], self)


def try_get(disk, sector0, parent):
    if sector0[3:11] == BootSector.SIGNATURE:
        return NTFS(disk, sector0, parent)
