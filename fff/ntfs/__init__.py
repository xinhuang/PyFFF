from .mft_entry import MFTEntry
from .boot_sector import BootSector
from .mft_attr import *


from ..entity import Entity
from ..data_units import DataUnits
from ..disk_view import DiskView

from tabulate import tabulate

import struct
from typing import Optional, List, Iterable, cast


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


class File(Entity):
    def __init__(self, mft_entry: MFTEntry, filesystem: NTFS):
        Entity.__init__(self)
        self.fs = filesystem
        self.mft_entry = mft_entry

    def attr(self, **kwargs) -> Optional[MFTAttr]:
        r = self.attrs(**kwargs)
        return r[0] if r else None

    def attrs(self, name: Optional[str] = None, type_id: Optional[str] = None) -> List[MFTAttr]:
        if name:
            return list([a for a in self.mft_entry.attrs if a.name == name])
        if type_id:
            return list([a for a in self.mft_entry.attrs if a.type_s == type_id])
        return self.mft_entry.attrs

    @property
    def name(self) -> str:
        attr = cast(mft_attr.FileName, self.attr(type_id='$FILE_NAME'))
        return attr.filename if attr is not None else ''

    @property
    def size(self) -> int:
        das = self.attrs(type_id='$DATA')
        return sum([da.actual_size for da in das])

    @property
    def allocated_size(self) -> int:
        das = self.attrs(type_id='$DATA')
        return sum([da.allocated_size for da in das])

    # TODO: Refactor the read interface in Entity
    def read2(self, count: int, skip: int = 0, bsize: int = 1) -> Iterable[bytes]:
        assert skip == 0, 'Skip is not supported yet'
        cluster_size = self.fs.cluster_size

        bytes_left = count * bsize
        attrs = self.attrs(type_id='$DATA')
        data_attrs = cast(List[mft_attr.Data], attrs)
        for dr in [dr for data_attr in data_attrs for dr in data_attr.data_runs]:
            # length, offset = dr
            to_read = min(bytes_left, dr.length * cluster_size)
            bytes_left -= to_read
            yield self.fs.read2(offset=dr.offset * self.fs.cluster_size, size=to_read)

    def tabulate(self) -> List[Sequence[Any]]:
        return [['File Name', self.name],
                ['inode', self.mft_entry.inode],
                ['Size', self.size],
                ['Allocated Size', self.allocated_size], ]

    def __str__(self):
        return tabulate(self.tabulate())

    def __repr__(self):
        return self.__str__()


class MFT(File):
    def __init__(self, filesystem: NTFS, data: bytes):
        mft_entry = MFTEntry(data, filesystem, 0)
        File.__init__(self, mft_entry, filesystem)

        self.mft_entries = {0: self.mft_entry}

    def find(self, name: Optional[str] = None, inode: Optional[int] = None) -> Optional[File]:
        bs = self.fs.cluster_size
        data = b''.join(self.read2(count=self.size))
        if name is not None:
            for i in range(1, len(data) // bs):
                e = MFTEntry(data[i*bs:(i+1)*bs], self.fs, i)
                self.mft_entries[i] = e
                f = File(e, self.fs)
                if f.name == name:
                    return f
        elif inode is not None:
            if inode >= len(data) // bs:
                raise Exception('inode too large')
            e = MFTEntry(data[inode*bs:(inode+1)*bs], self.fs, inode)
            self.mft_entries[inode] = e
            return File(e, self.fs)
        return None


def try_get(disk: DiskView, sector0: bytes, parent) -> Optional[NTFS]:
    if sector0[3: 11] == BootSector.SIGNATURE:
        return NTFS(disk, sector0, parent)
    else:
        return None
