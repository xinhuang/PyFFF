from .entity import Entity
from .data_units import DataUnits
from . import filesystem

from tabulate import tabulate

import struct
from functools import reduce
import operator


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
        Entity.__init__(self, parent.dv.disk,
                        sector_offset * parent.sector_size,
                        sector_count * parent.sector_size,
                        parent.sector_size, number, parent)

        self.ebr = None
        self.sectors = DataUnits(self, self.sector_size, self.sector_count)

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
