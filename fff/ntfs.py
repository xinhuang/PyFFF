import struct
from tabulate import tabulate


NTFS_SIGNATURE = b'NTFS    '


class BootSector(object):
    def __init__(self, sector0):
        self.data = sector0[0:0x200]
        self.jmp = sector0[0:3]
        self.signature = sector0[3:11]

        assert self.signature == NTFS_SIGNATURE

        self.bytes_per_sector = struct.unpack('<H', sector0[11:13])[0]
        self.sectors_per_cluster = sector0[13]

        # TODO: parse unused/reserved fields
        self.media_descriptor = sector0[0x15]
        self.sectors_per_track = struct.unpack('<H', sector0[0x18:0x1A])[0]

    def tabulate(self):
        return [['JMP', self.jmp],
                ['Signature', self.signature],
                ['Bytes Per Sector', self.bytes_per_sector]]

    def __str__(self):
        return tabulate(self.tabulate(),
                        headers=['Field', 'Value'])


class NTFS(object):
    def __init__(self, disk, sector0):
        self.boot_sector = BootSector(sector0)


def try_get(disk, sector0):
    if sector0[3:11] == NTFS_SIGNATURE:
        return NTFS(disk, sector0)
