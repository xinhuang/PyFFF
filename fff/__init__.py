from . import filesystem
from .disk_view import DiskView
from .entity import Entity
from .unallocated_space import UnallocatedSpace

from tabulate import tabulate
from hexdump import hexdump as hd

import struct
import operator
from functools import reduce


EXTENDED_PARTITION_TYPES = set([0x05, 0x0F])

# https://www.win.tue.nl/~aeb/partitions/partition_types-1.html
PARTITION_TYPES = {
    0x00: 'Unused Partition Table Entry',
    0x01: 'DOS 12-bit FAT',

    0x04: '04 DOS 3.0+ 16-bit FAT (up to 32M)',
    0x05: 'DOS 3.3+ Extended Partition',
    0x06: '06 DOS 3.31+ 16-bit FAT (over 32M)',
    0x07: '07 Windows NT NTFS/exFAT/Advanced Unix/QNX2.x pre-1988',

    0x0B: 'WIN95 OSR2 FAT32',
    0x0C: 'WIN95 OSR2 FAT32, LBA-mapped',

    0x0E: 'WIN95: DOS 16-bit FAT, LBA-mapped',
    0x0F: 'WIN95: Extended partition, LBA-mapped',

    0x82: 'Linux swap',
    0x83: 'Linux native partition',

    0x85: 'Linux extended partition',
}


class CHS(object):
    def __init__(self, data):
        self.h = data[0]
        self.s = data[1] & 0b00111111
        self.c = ((data[1] & 0b11000000) << 2) | data[2]

    def __str__(self):
        return '{}/{}/{}'.format(self.c, self.h, self.s)


class Partition(Entity):
    def __init__(self, data, number, parent):
        self.data = data

        self.bootable_flag = struct.unpack('<B', data[0:1])[0]
        self.partition_type = struct.unpack('<B', data[4:5])[0]

        self.start_chs = CHS(data[1:4])
        self.end_chs = CHS(data[5:8])

        sector_offset = struct.unpack('<I', data[8:12])[0] + parent.sector_offset
        sector_count = struct.unpack('<I', data[12:16])[0]
        last_sector = sector_offset + sector_count - 1
        Entity.__init__(self, parent.dv.disk, sector_offset, last_sector,
                        parent.sector_size, number, parent)

        self.ebr = None

    @property
    def sectors(self):
        class SectorContainer(object):
            def __init__(self, partition):
                self.partition = partition

            def __getitem__(self, index_or_slice):
                sector_size = self.partition.sector_size
                if isinstance(index_or_slice, int):
                    index = index_or_slice
                    return self.partition.read(index, sector_size)
                elif isinstance(index_or_slice, slice):
                    s = index_or_slice
                    n = s.stop - s.start
                    return self.partition.read(s.start * sector_size,
                                               n * sector_size)
        return SectorContainer(self)

    @property
    def is_bootable(self):
        return (self.bootable_flag & 0x80) != 0

    @property
    def is_extended(self):
        return self.partition_type in EXTENDED_PARTITION_TYPES

    @property
    def is_unallocated(self):
        return self.partition_type == 0x00

    @property
    def description(self):
        default = 'Extended Partition' if self.is_extended else 'Partition'
        return '{} ({})'.format(PARTITION_TYPES.get(self.partition_type, default),
                                hex(self.partition_type))

    @property
    def _max_index(self):
        if not self.is_extended:
            return self.index
        else:
            return max([self.ebr._max_index])

    def hexdump(self):
        return hd(self.data)

    @property
    def filesystem(self):
        return filesystem.get_filesystem(self.dv)

    def read(self, offset, size):
        self.dv.seek(offset)
        return self.dv.read(size)

    @property
    def entities(self):
        yield self
        if self.is_extended:
            for e in self.ebr.entities:
                yield e

    def tabulate(self):
        return [[self.index,
                 '{}:{}'.format(self.parent.number, self.number),
                 self.sector_offset,
                 self.last_sector if not self.is_unallocated else '-',
                 self.sector_count,
                 self.description,
                 'CHS {} - {}'.format(self.start_chs, self.end_chs)]]

    def __str__(self):
        rows = reduce(operator.add, [e.tabulate() for e in self.entities])
        return tabulate(rows,
                        headers=['#', 'Slot', 'Start', 'End', 'Length',
                                 'Description', 'CHS', ])


class MBR(object):
    def __init__(self, disk_view, number=0, parent=None):
        self.sector_offset = parent.sector_offset if parent else 0
        self.number = number
        self.sector_size = 512
        self.dv = disk_view
        self.parent = parent
        self.index = -1 if parent else 0

        self.unallocated = []
        self.unused_entries = []

        data = self.read(0, 512)

        self.boot_code = struct.unpack('<446B', data[0:446])
        self.signature = struct.unpack('<H', data[510:])[0]

        assert self.signature == 0xAA55

        self.partitions = []
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
                    dv = DiskView(self.dv.disk, p.sector_offset * self.sector_size, p.size)
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
    def last_sector(self):
        return self.sector_offset

    @property
    def _max_number(self):
        return max([p.ebr.number for p in self.partitions if p.is_extended] +
                   [self.number])

    @property
    def _max_index(self):
        return max([p._max_index for p in self.partitions] + [self.index])

    @property
    def entities(self):
        yield self

        children = sorted(self.unallocated + [p for p in self.partitions],
                          key=lambda e: e.sector_offset)
        for c in children:
            for e in c.entities:
                yield e

        for e in self.unused_entries:
            yield e

    def __getitem__(self, i):
        assert isinstance(i, int)

        for e in self.entities:
            if e.index == i:
                return e

    def read(self, offset, size):
        self.dv.seek(offset)
        data = self.dv.read(size)
        return data

    def _init_unallocated(self):
        self.unallocated = []
        ps = sorted(self.partitions.copy(),
                    key=lambda p: p.sector_offset)

        if len(ps) == 0:
            if self.sector_offset < self.last_sector:
                us = UnallocatedSpace(self.sector_offset + 1, self.last_sector, parent=self)
                self.unallocated.append(us)
        else:
            if self.sector_offset + 1 < ps[0].sector_offset:
                us = UnallocatedSpace(self.sector_offset + 1,
                                      ps[0].sector_offset - 1,
                                      parent=self)
                self.unallocated.append(us)

            for i in range(1, len(ps)):
                prev = ps[i - 1]
                curr = ps[i]
                if prev.last_sector + 1 < curr.sector_offset:
                    us = UnallocatedSpace(prev.last_sector + 1,
                                          curr.sector_offset - 1,
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
                 self.sector_offset, self.sector_offset, 1, self.description]]

    def __str__(self):
        rows = reduce(operator.add, [e.tabulate() for e in self.entities])
        return tabulate(rows,
                        headers=['#', 'Slot', 'Start', 'End', 'Length', 'Description'])


class DiskImage(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self._file = open(filepath, 'rb')
        self._file.seek(0, 2)
        dv = DiskView(self._file, 0, self._file.tell())
        self.volume = MBR(dv)

    def close(self):
        self._file.close()
