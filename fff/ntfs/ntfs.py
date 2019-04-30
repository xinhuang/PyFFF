from .mft import MFT
from .boot_sector import BootSector
from .file import File

from ..entity import Entity
from ..data_units import DataUnits
from ..disk_view import DiskView

from typing import Optional


class NTFS(object):
    def __init__(self, dv: DiskView, sector0: bytes, parent):
        # Entity.__init__(self)
        self.boot_sector = BootSector(sector0)
        bs = self.boot_sector
        self.dv = DiskView(dv.disk, dv.begin, dv.size,
                           sector_size=self.sector_size,
                           cluster_size=self.cluster_size)

        self.fs_type = 'NTFS'

        self.sectors = self.dv.sectors

        self.clusters = self.dv.clusters

        i = self.boot_sector.mft_cluster_number
        n = self.boot_sector.cluster_per_file_record_segment
        self.mft = MFT(self, self.clusters[i:i+n])

        e = self.mft.find(inode=5)
        assert e
        self.root = File(e, self)

    def find(self, inode: Optional[int] = None, name: Optional[str] = None) -> Optional[File]:
        e = self.mft.find(inode=inode, name=name)
        return File(e, self) if e else None

    @property
    def sector_size(self):
        return self.boot_sector.bytes_per_sector

    @property
    def cluster_size(self):
        return self.boot_sector.cluster_size

    def read(self, size: int, offset: int) -> bytes:
        return self.dv.read(offset=offset, size=size)
