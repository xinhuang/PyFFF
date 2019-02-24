from tabulate import tabulate

import struct


EXTENDED_PARTITION_TYPES = {
    0x05: 'DOS 3.3+ Extended Partition',
    0x0F: 'WIN95: Extended partition, LBA-mapped',
}


class Partition(object):
    def __init__(self, data, parent=None):
        self.parent = parent
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
    def is_bootable(self):
        return (self.bootable_flag & 0x80) != 0

    @property
    def is_extended(self):
        return self.partition_type in EXTENDED_PARTITION_TYPES

    def tabulate(self):
        if self.is_extended:
            return [[self.sector_offset,
                     self.sector_offset + self.total_sector,
                     self.total_sector,
                     'Extended Partition ({})'.format(hex(self.partition_type))]] + self.ebr.tabulate()
        else:
            return [[self.sector_offset,
                     self.sector_offset + self.total_sector,
                     self.total_sector,
                     'Partition ({})'.format(hex(self.partition_type))]]


class MBR(object):
    def __init__(self, disk, parent=None):
        self.sector_size = 512
        self.parent = parent
        self.sector_offset = parent.sector_offset if parent else 0

        disk.seek(self.sector_offset * self.sector_size)
        data = disk.read(512)

        self.boot_code = struct.unpack('<446B', data[0:446])
        self.signature = struct.unpack('<H', data[510:])[0]

        assert self.signature == 0xAA55

        self.partitions = [
            Partition(data[446:462], parent=self),
            Partition(data[462:478], parent=self),
            Partition(data[478:494], parent=self),
            Partition(data[494:510], parent=self),
        ]
        for p in [p for p in self.partitions if p.is_extended]:
            p.ebr = MBR(disk, parent=p)

    def tabulate(self):
        return [[self.sector_offset, self.sector_offset, 1, 'MBR/EBR']] + [i for p in self.partitions for i in p.tabulate()]

    def __str__(self):
        return tabulate(self.tabulate(), headers=['Start', 'End', 'Length', 'Description'])


class DiskImage(object):
    def __init__(self, filepath):
        self.filepath = filepath
        with open(filepath, 'rb') as disk:
            self.volume = MBR(disk)
