from .mft import MFT
from .boot_sector import BootSector

from ..entity import Entity
from ..data_units import DataUnits
from ..disk_view import DiskView


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

    @property
    def cluster_size(self):
        return self.boot_sector.cluster_size

    # TODO:
    def read2(self, size: int, offset: int) -> bytes:
        return self.dv.read(offset=offset, size=size)
