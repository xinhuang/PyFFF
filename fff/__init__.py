from . import filesystem

from tabulate import tabulate
from hexdump import hexdump as hd

import struct


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


class DiskIO(object):
    def __init__(self, io, begin, size):
        self.io = io
        self._begin = begin
        self._end = begin + size

        assert self._begin <= self._end

    @property
    def size(self):
        return self._end - self._begin

    def seek(self, offset):
        location = self._begin + offset
        assert location >= self._begin and location < self._end
        self.io.seek(location)

    def read(self, size):
        assert self.io.tell() + size < self._end
        return self.io.read(size)


class UnallocatedSpace(object):
    def __init__(self, sector_offset, total_sector):
        self.sector_offset = sector_offset
        self.total_sector = total_sector

    @property
    def last_sector(self):
        return self.sector_offset + self.total_sector - 1

    @property
    def is_extended(self):
        return False

    def tabulate(self):
        return [[self.sector_offset,
                 self.sector_offset + self.total_sector,
                 self.total_sector,
                 'Unallocated']]


class Partition(object):
    def __init__(self, data, parent=None):
        self.parent = parent
        self.data = data
        self.bootable_flag = struct.unpack('<B', data[0:1])[0]

        self.partition_type = struct.unpack('<B', data[4:5])[0]

        # FIXME: get the coorect CHS
        self.start_chs = struct.unpack('<BH', data[1:4])[0]
        self.end_chs = struct.unpack('<BH', data[5:8])[0]

        self._sector_offset = struct.unpack('<I', data[8:12])[0]
        self.total_sector = struct.unpack('<I', data[12:16])[0]

        self.ebr = None

    @property
    def sector_offset(self):
        parent_offset = self.parent.sector_offset if self.parent else 0
        return self._sector_offset + parent_offset

    @property
    def last_sector(self):
        return self.sector_offset + self.total_sector - 1

    @property
    def is_bootable(self):
        return (self.bootable_flag & 0x80) != 0

    @property
    def is_extended(self):
        return self.partition_type in EXTENDED_PARTITION_TYPES

    @property
    def description(self):
        default = 'Extended Partition' if self.is_extended else 'Partition'
        return '{} ({})'.format(PARTITION_TYPES.get(self.partition_type, default),
                                hex(self.partition_type))

    def hexdump(self):
        return hd(self.data)

    def get_filesystem(self):
        return filesystem.get_filesystem(self.get_disk_reader())

    def get_disk_reader(self):
        return DiskIO(self.parent.disk,
                      self.sector_offset * self.parent.sector_size,
                      self.total_sector * self.parent.sector_size)

    def tabulate(self):
        return [[self.sector_offset,
                 self.sector_offset + self.total_sector,
                 self.total_sector,
                 self.description]] + (self.ebr.tabulate() if self.is_extended else [])

    def __str__(self):
        return tabulate(self.tabulate(), headers=['Start', 'End', 'Length', 'Description'])


class MBR(object):
    def __init__(self, disk, parent=None):
        self.sector_size = 512
        self.disk = disk
        self.parent = parent
        self.sector_offset = parent.sector_offset if parent else 0

        data = self.read_data()

        self.boot_code = struct.unpack('<446B', data[0:446])
        self.signature = struct.unpack('<H', data[510:])[0]

        assert self.signature == 0xAA55

        self.partitions = [Partition(data[446:462], parent=self)]

        # FIXME: partitions may not be ordered by start offset
        for start in [462, 478, 494]:
            curr = Partition(data[start:start+16], parent=self)
            prev = self.partitions[-1]
            if curr.sector_offset != prev.last_sector + 1:
                self.partitions.append(UnallocatedSpace(prev.last_sector + 1,
                                                        curr.sector_offset - prev.last_sector - 1))
            self.partitions.append(curr)

        for p in [p for p in self.partitions if p.is_extended]:
            p.ebr = MBR(disk, parent=p)

    @property
    def description(self):
        return 'EBR' if self.parent else 'MBR'

    def read_data(self):
        self.disk.seek(self.sector_offset * self.sector_size)
        data = self.disk.read(512)
        return data

    def hexdump(self):
        data = self.read_data()
        return hd(data)

    def tabulate(self):
        return ([[self.sector_offset, self.sector_offset, 1, self.description]] +
                [i for p in self.partitions for i in p.tabulate()])

    def __str__(self):
        return tabulate(self.tabulate(), headers=['Start', 'End', 'Length', 'Description'])


class DiskImage(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self._file = open(filepath, 'rb')
        self.volume = MBR(self._file)

    def close(self):
        self._file.close()
