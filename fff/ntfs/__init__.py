from .mft_entry import MFTEntry
from .boot_sector import BootSector


from ..entity import Entity
from ..data_units import DataUnits
from ..disk_view import DiskView

from tabulate import tabulate

import struct
from typing import Optional


class File(Entity):
    def __init__(self, mft_entry: MFTEntry, filesystem: Entity):
        Entity.__init__(self)
        self.mft_entry = mft_entry


class MFT(File):
    def __init__(self, filesystem: Entity, data: bytes):
        mft_entry = MFTEntry(data, filesystem)
        File.__init__(self, mft_entry, filesystem)

        self.mft_entries = [self.mft_entry]


class NTFS(Entity):
    def __init__(self, dv: DiskView, sector0: bytes, parent):
        Entity.__init__(self)
        self.boot_sector = BootSector(sector0)
        self.dv = dv

        self.fs_type = 'NTFS'

        bs = self.boot_sector

        self.sectors = DataUnits(self, bs.bytes_per_sector,
                                 dv.size // bs.bytes_per_sector)

        cluster_size = self.sector_size * bs.sectors_per_cluster
        cluster_count = bs.total_sectors // bs.sectors_per_cluster
        self.clusters = DataUnits(self, cluster_size, cluster_count)

        i = self.boot_sector.mft_cluster_number
        n = self.boot_sector.cluster_per_file_record_segment
        self.mft = MFT(self, self.clusters[i:i+n])

    @property
    def sector_size(self):
        return self.boot_sector.bytes_per_sector


def try_get(disk: DiskView, sector0: bytes, parent) -> Optional[NTFS]:
    if sector0[3:11] == BootSector.SIGNATURE:
        return NTFS(disk, sector0, parent)
    else:
        return None
