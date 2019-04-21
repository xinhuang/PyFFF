from .mft_entry import MFTEntry
from .mft_attr import FileName, Data, IndexAllocation, IndexRoot, MFTAttr

from ..entity import Entity

from tabulate import tabulate

from typing import Optional, cast, List, Iterable, Sequence, Any


class File(Entity):
    def __init__(self, mft_entry: MFTEntry, filesystem):
        Entity.__init__(self)
        self.fs = filesystem
        self.mft_entry = mft_entry

    def attr(self, **kwargs) -> Optional[MFTAttr]:
        r = self.attrs(**kwargs)
        return r[0] if r else None

    def attrs(self, name: Optional[str] = None, type_id: Optional[str] = None) -> List[MFTAttr]:
        return self.mft_entry.attrs(name=name, type_id=type_id)

    @property
    def inode(self) -> int:
        return self.mft_entry.inode

    @property
    def name(self) -> str:
        attr = cast(FileName, self.attr(type_id='$FILE_NAME'))
        return attr.filename if attr is not None else ''

    @property
    def size(self) -> int:
        das = self.attrs(type_id='$DATA')
        return sum([da.header.actual_size for da in das])

    @property
    def allocated_size(self) -> int:
        das = self.attrs(type_id='$DATA')
        return sum([da.header.allocated_size for da in das])

    @property
    def is_file(self):
        return self.mft_entry.is_file

    @property
    def is_dir(self):
        return self.mft_entry.is_dir

    @property
    def is_allocated(self):
        return self.mft_entry.in_use

    def list(self) -> 'List[File]':
        if self.is_file:
            return []

        files: List[File] = []
        ir = self.mft_entry.attr(type_id='$INDEX_ROOT')
        assert ir
        ir = cast(IndexRoot, ir)
        for e in ir.entries:
            if not e.is_last:
                files.append(self.fs.find(inode=e.file_ref.inode))
        ias = self.mft_entry.attrs(type_id='$INDEX_ALLOCATION')
        for e in [e for ia in ias
                  for r in cast(IndexAllocation, ia).records.values()
                  for e in r.entries]:
            if not e.is_last:
                files.append(self.fs.find(inode=e.file_ref.inode))
        return files

    # TODO: Refactor the read interface in Entity
    def read2(self, count: int, skip: int = 0, bsize: int = 1) -> Iterable[bytes]:
        assert skip == 0, 'Skip is not supported yet'
        cluster_size = self.fs.cluster_size

        bytes_left = count * bsize
        attrs = self.attrs(type_id='$DATA')
        data_attrs = cast(List[Data], attrs)
        for dr in [dr for data_attr in data_attrs for dr in data_attr.header.vcn.drs]:
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
