from .disk_view import DiskView
from .entity import Entity
from .unallocated_space import UnallocatedSpace
from .partition import Partition

from tabulate import tabulate
from hexdump import hexdump as hd
import filetype

import struct
import operator
from functools import reduce
from zipfile import ZipFile
import gzip
from typing import Sequence


class MBR(Entity):

    SECTOR_SIZE = 512

    def __init__(self, disk_view, number: int = 0, parent=None):
        disk = disk_view.disk
        offset = disk_view.begin
        size = disk_view.size
        Entity.__init__(self)

        self.dv = disk_view
        self.number = number
        self.parent = parent
        self.first_sector = disk_view.begin // MBR.SECTOR_SIZE
        self.last_sector = self.first_sector + size // MBR.SECTOR_SIZE

        self.unallocated: Sequence[UnallocatedSpace] = []
        self.unused_entries: Sequence[Partition] = []
        self.partitions: Sequence[Partition] = []

        data = disk_view.read(512, offset=0)

        self.boot_code = struct.unpack('<446B', data[0:446])
        self.signature = struct.unpack('<H', data[510:])[0]

        assert self.signature == 0xAA55

        slices = [slice(446, 462), slice(462, 478), slice(478, 494), slice(494, 510)]
        n = self.number + 1
        for i in range(4):
            s = slices[i]
            p = Partition(data[s], number=i, parent=self)
            if p.partition_type == 0:
                self.unused_entries.append(p)
            else:
                self.partitions.append(p)

                if p.is_extended:
                    dv = DiskView(self.dv.disk, p.first_sector * self.sector_size, p.size)
                    p.ebr = MBR(dv, number=n, parent=p)
                    n = p.ebr._max_number

        self._init_unallocated()

        if parent is None:
            i = 1
            for e in self.entities:
                e.index = i
                i += 1

    @property
    def description(self):
        return 'Extended Boot Record' if self.parent else 'Master Boot Record'

    @property
    def _max_number(self):
        return max([p.ebr.number for p in self.partitions if p.is_extended] +
                   [self.number])

    @property
    def entities(self):
        yield self

        children = sorted(self.unallocated + [p for p in self.partitions],
                          key=lambda e: e.first_sector)
        for c in children:
            for e in c.entities:
                yield e

        for e in self.unused_entries:
            yield e

    @property
    def sector_size(self):
        return MBR.SECTOR_SIZE

    def __getitem__(self, i):
        assert isinstance(i, int)

        for e in self.entities:
            if e.index == i:
                return e

    def _init_unallocated(self):
        self.unallocated = []
        ps = sorted(self.partitions.copy(),
                    key=lambda p: p.first_sector)

        if len(ps) == 0:
            if self.first_sector < self.last_sector:
                us = UnallocatedSpace(self.first_sector + 1,
                                      self.last_sector, parent=self)
                self.unallocated.append(us)
        else:
            if self.first_sector + 1 < ps[0].first_sector:
                us = UnallocatedSpace(self.first_sector + 1,
                                      ps[0].first_sector - 1,
                                      parent=self)
                self.unallocated.append(us)

            for i in range(1, len(ps)):
                prev = ps[i - 1]
                curr = ps[i]
                if prev.last_sector + 1 < curr.first_sector:
                    us = UnallocatedSpace(prev.last_sector + 1,
                                          curr.first_sector - 1,
                                          parent=self)
                    self.unallocated.append(us)

            if ps[-1].last_sector < self.last_sector:
                us = UnallocatedSpace(ps[-1].last_sector + 1,
                                      self.last_sector, parent=self)
                self.unallocated.append(us)

    def hexdump(self):
        data = self.read(0, 512)
        return hd(data)

    def tabulate(self):
        return [[self.index, self.number,
                 self.first_sector, self.first_sector, 1, self.description]]

    def __str__(self):
        rows = reduce(operator.add, [e.tabulate() for e in self.entities])
        return tabulate(rows,
                        headers=['#', 'Slot', 'Start', 'End', 'Length', 'Description'])

    def __repr__(self):
        return self.__str__()


class DiskImage(object):
    def __init__(self, filepath):
        self.filepath = filepath

        kind = filetype.guess(self.filepath)
        self.mime = kind.mime if kind else 'n/a'
        if kind is None:
            self._archive = None
            self._file = open(filepath, 'rb')
        elif kind.mime == 'application/zip':
            self._archive = ZipFile(self.filepath)
            first_file = self._archive.namelist()[0]
            self._file = self._archive.open(first_file)
        elif kind.mime == 'application/gzip':
            self._archive = None
            self._file = gzip.open(self.filepath)
        else:
            assert 'Unsupported MIME: {}'.format(kind.mime) and False

        self._file.seek(0, 2)
        dv = DiskView(self._file, 0, self._file.tell())
        self.volume = MBR(dv)

    def close(self):
        self._file.close()
        if self._archive:
            self._archive.close()
