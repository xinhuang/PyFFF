from .mft_entry import MFTEntry
from .mft_attr import MFTAttr, FileName, Data

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
        if name:
            return list([a for a in self.mft_entry.attrs if a.name == name])
        if type_id:
            return list([a for a in self.mft_entry.attrs if a.type_s == type_id])
        return self.mft_entry.attrs

    @property
    def name(self) -> str:
        attr = cast(FileName, self.attr(type_id='$FILE_NAME'))
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
        data_attrs = cast(List[Data], attrs)
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
