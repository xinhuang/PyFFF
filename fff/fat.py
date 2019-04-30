import struct

from tabulate import tabulate


class BootSector(object):
    def __init__(self, disk, sector0):
        self.data = sector0
        self.jump = sector0[0:3]
        self.oem = sector0[3:11]
        self.bytes_per_sector = struct.unpack('<H', sector0[11:13])[0]
        self.sectors_per_cluster = sector0[13]
        self.reserved_sectors = struct.unpack('<H', sector0[14:16])[0]
        self.nfats = sector0[16]
        self.max_files_in_root = struct.unpack('<H', sector0[17:19])[0]
        self.nsectors16 = struct.unpack('<H', sector0[19:21])[0]
        self.media_type = sector0[21]
        self.fat_size = struct.unpack('<H', sector0[22:24])[0]
        self.sectors_per_track = struct.unpack('<H', sector0[24:26])[0]
        self.nheads = struct.unpack('<H', sector0[26:28])[0]
        self.sectors_before_partition = struct.unpack('<I', sector0[28:32])[0]
        self.nsectors32 = struct.unpack('<I', sector0[32:36])[0]

        self.sector_count = self.nsectors16 + self.nsectors32 << 16

    @property
    def media_type_s(self):
        pass

    def tabulate(self):
        return [['JMP', self.jump.hex()],
                ['OEM', self.oem.hex()],
                ['Bytes per Sector', self.bytes_per_sector],
                ['Sectors per Cluster', self.sectors_per_cluster],
                ['Reserved Sectors', self.reserved_sectors],
                ['#FAT', self.nfats],
                ['Max Files in Root', self.max_files_in_root],
                ['#Sectors', self.sector_count],
                ['Media Type', self.media_type_s],
                ['FAT Size', self.fat_size],
                ['Sectors per Track', self.sectors_per_track],
                ['#Heads', self.nheads],
                ['Sectors Before Partition', self.sectors_before_partition], ]

    def __str__(self):
        return tabulate(self.tabulate())

    def __repr__(self):
        return self.__str__()


class FAT(object):
    def get_version(sector0, size):
        # FIXME: verify cluster count calculation
        sector_size = struct.unpack('<H', sector0[11:13])[0]
        sector_per_cluster = struct.unpack('<B', sector0[13:14])[0]
        cluster_size = sector_size * sector_per_cluster
        if cluster_size == 0:
            return None
        clusters = size / cluster_size
        if clusters < 4085:
            return 12
        elif clusters < 65525:
            return 16
        else:
            return 32

    def tabulate(self):
        return self.boot_sector.tabulate()

    def __str__(self):
        return tabulate(self.tabulate())

    def __repr__(self):
        return self.__str__()


class FAT12(FAT):
    def __init__(self, disk, data):
        self.boot_sector = BootSector(disk, data)
        self.fs_type = 'FAT12'


class FAT16(FAT):
    def __init__(self, disk, data):
        self.boot_sector = BootSector(disk, data)
        self.fs_type = 'FAT16'


class FAT32(FAT):
    def __init__(self, disk, data):
        self.boot_sector = BootSector(disk, data)
        self.fs_type = 'FAT32'


def try_get(disk, sector0, parent):
    if sector0[-2] == 0x55 and sector0[-1] == 0xAA:
        ver = FAT.get_version(sector0, disk.size)
        if ver == 12:
            return FAT12(disk, sector0)
        elif ver == 16:
            return FAT16(disk, sector0)
        elif ver == 32:
            return FAT32(disk, sector0)
        else:
            assert False and 'Unknown FAT version'
