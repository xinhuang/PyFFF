from .mft_entry import MFTEntry
from .mft_attr import FileName, Data, IndexAllocation, IndexRoot, MFTAttr

from ..entity import Entity
from ..abstract_file import AbstractFile
from .. import previewer

from tabulate import tabulate
import magic

from typing import Optional, cast, List, Iterable, Sequence, Any, Pattern
from itertools import chain
import fnmatch
import re
from os import path


class File(AbstractFile):
    def __init__(self, mft_entry: MFTEntry, filesystem):
        super().__init__()
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
        attrs = cast(List[FileName], self.attrs(type_id='$FILE_NAME'))
        win32 = next((a for a in attrs if (a.namespace & 1) != 0), None)
        if win32:
            return win32.filename
        dos = next((a for a in attrs if a.namespace == 2), None)
        if dos:
            return dos.filename
        return attrs[0].filename if attrs else ''

    @property
    def size(self) -> int:
        das = self.attrs(type_id='$DATA', name='')
        return sum([da.header.actual_size for da in das])

    @property
    def allocated_size(self) -> int:
        das = self.attrs(type_id='$DATA', name='')
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

    @property
    def parent(self):
        fn = cast(FileName, self.attr(type_id='$FILE_NAME'))
        pid = fn.parent.inode
        if pid == self.mft_entry.inode:
            return None
        else:
            return self.fs.find(inode=pid)

    @property
    def fullpath(self) -> str:
        if self.name == '.':
            return '/'

        r = self.name
        p = self.parent
        while p.name != '.':
            r = path.join(p.name, r)
            p = p.parent
        return '/' + r

    @property
    def slack_space(self) -> bytes:
        size = self.allocated_size - self.size
        return b''.join(self.read(count=size, skip=self.size))

    @property
    def mime(self) -> str:
        return magic.from_buffer(b''.join(self.read(count=261)), mime=True)

    @property
    def data(self) -> bytes:
        return b''.join(self.read(self.size))

    def list(self, recursive: bool = False, pattern: str = None, regex: str = None,
             _reobj: Pattern = None) -> 'Iterable[File]':
        if self.is_file:
            return

        assert not (pattern and regex)

        if pattern:
            regex = fnmatch.translate(pattern)
        if regex:
            assert not _reobj
            _reobj = re.compile(regex)

        ir = self.mft_entry.attr(type_id='$INDEX_ROOT')
        assert ir
        ir = cast(IndexRoot, ir)
        ias = self.mft_entry.attrs(type_id='$INDEX_ALLOCATION')

        entries = chain(ir.entries,
                        (e for ia in ias
                         for r in cast(IndexAllocation, ia).records.values()
                         for e in r.entries))

        for e in entries:
            if not e.is_last:
                f = self.fs.find(inode=e.file_ref.inode)
                if not _reobj or _reobj.search(f.name):
                    yield f
                if f.is_dir and recursive and f.mft_entry.inode != self.mft_entry.inode:
                    for sub in f.list(recursive=recursive, _reobj=_reobj):
                        if not _reobj or _reobj.search(sub.name):
                            yield sub

    def read(self, count: int, skip: int = 0, bsize: int = 1) -> Iterable[bytes]:
        cluster_size = self.fs.cluster_size
        skip *= bsize

        bytes_left = count * bsize
        attrs = self.attrs(type_id='$DATA', name='')
        data_attrs = cast(List[Data], attrs)
        for dr in [dr for data_attr in data_attrs for dr in data_attr.header.vcn.drs]:
            consec_size = dr.length * cluster_size
            if skip >= consec_size:
                skip -= consec_size
            else:
                to_read = min(skip + bytes_left, consec_size)
                bytes_left = bytes_left - to_read + skip
                yield self.fs.read(offset=dr.offset * self.fs.cluster_size, size=to_read)[skip:]

    def contains(self, cluster: int) -> bool:
        attrs = self.attrs(type_id='$DATA', name='')
        data_attrs = cast(List[Data], attrs)
        for dr in [dr for data_attr in data_attrs for dr in data_attr.header.vcn.drs]:
            if not dr.offset:
                continue
            if cluster >= dr.offset and cluster < dr.offset + dr.length:
                return True
        return False

    def tabulate(self) -> List[Sequence[Any]]:
        return [['Name', self.name],
                ['inode', self.mft_entry.inode],
                ['Type', 'File' if self.is_file else 'Dir'],
                ['Size', self.size],
                ['Allocated Size', self.allocated_size], ]

    def preview(self):
        previewer.preview(self)

    def __str__(self):
        return '{} {:>8} "{}" {}'.format('r' if self.is_file else 'd',
                                         self.mft_entry.inode, self.name, self.size)

    def __repr__(self):
        return self.__str__()
