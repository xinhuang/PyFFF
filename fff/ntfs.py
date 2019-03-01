from .entity import Entity
from .data_units import DataUnits

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

        self.media_descriptor = sector0[0x15]
        self.sectors_per_track = struct.unpack('<H', sector0[0x18:0x18+2])[0]
        self.number_of_heads = struct.unpack('<H', sector0[0x1A:0x1A+2])[0]
        self.hidden_sectors = struct.unpack('<I', sector0[0x1C:0x1C+4])[0]

        self.total_sectors = struct.unpack('<Q', sector0[0x28:0x28+8])[0]
        self.mft_cluster_number = struct.unpack('<Q', sector0[0x30:0x30+8])[0]
        self.mftmirr_cluster_number = struct.unpack('<Q', sector0[0x38:0x38+8])[0]
        self.cluster_per_file_record_segment = self._decode_size(
            struct.unpack('<b', sector0[0x40:0x41])[0])

        self.cluster_per_index_buffer = self._decode_size(
            struct.unpack('<b', sector0[0x44:0x45])[0])

        self.volume_serial_number = struct.unpack('<Q', sector0[0x48:0x48+8])[0]

        self.bootstrap_code = sector0[0x54:0x54+426]
        self.marker = sector0[0x1FE:0x1FE+2]

    @property
    def cluster_size(self):
        return self.bytes_per_sector * self.sectors_per_cluster

    def _decode_size(self, value):
        if value >= 0:
            return value
        else:
            return 2 ** -value / self.cluster_size

    def tabulate(self):
        return [['JMP', self.jmp.hex()],
                ['Signature', '{}({})'.format(self.signature.decode(),
                                              self.signature.hex())],
                ['Bytes Per Sector', self.bytes_per_sector],
                ['Sectors Per Cluster', self.sectors_per_cluster],
                ['...', '...'],
                ['Media Descriptor', self.media_descriptor],
                ['Sectors Per Track', self.sectors_per_track],
                ['Number of Heads', self.number_of_heads],
                ['Hidden Sectors', self.hidden_sectors],
                ['...', '...'],
                ['Total Sectors', self.total_sectors],
                ['$MFT Cluster Number', self.mft_cluster_number],
                ['$MFTMirr Cluster Number', self.mftmirr_cluster_number],
                ['Cluster Per File Record Segment', self.cluster_per_file_record_segment],
                ['...', '...'],
                ['Cluster Per Index Buffer', self.cluster_per_index_buffer],
                ['...', '...'],
                ['Volume Serial Number', self.volume_serial_number],
                ['...', '...'],
                ['Bootstrap Code', self.bootstrap_code[:10].hex()],
                ['Marker', self.marker.hex()], ]

    def __str__(self):
        return tabulate(self.tabulate(),
                        headers=['Field', 'Value'])

    def __repr__(self):
        return self.__str__()


class MFTAttribute(object):

    # http://www.cse.scu.edu/~tschwarz/coen252_07Fall/Lectures/NTFS.html
    TYPES = {
        0x10: '$STANDARD_INFORMATION',
        0x20: '$ATTRIBUTE_LIST',
        0x30: '$FILE_NAME',
        0x40: '$VOLUME_VERSION',
        0x50: '$OBJECT_ID',
        0x60: '$VOLUME_NAME',
        0x70: '$VOLUME_INFORMATION',
        0x80: '$DATA',
        0x90: '$INDEX_ROOT',
        0xA0: '$INDEX_ALLOCATION',
        0xB0: '$BITMAP',
        0xC0: '$SYMBOLIC_LINK(NT) | $REPARSE_POINT(2K)',
        0xD0: '$EA_INFORMATION',
        0xE0: '$EA',
        0xF0: '$PROPERTY_SET',
        0x100: '$LOGGED_UTILITY_STREAM',
    }

    def __init__(self, data, offset):
        self.type_id = struct.unpack('<I', data[offset:offset+4])[0]
        self.size = struct.unpack('<I', data[offset+4:offset+8])[0]
        self.nr_flag = data[offset+8]
        self.name_length = data[offset+9]
        self.name_offset = struct.unpack('<H', data[offset+10:offset+12])[0]
        self.flags = struct.unpack('<H', data[offset+12:offset+14])[0]
        self.attr_id = struct.unpack('<H', data[offset+14:offset+16])[0]

        self.data = data[offset:offset+self.size]

    @property
    def type_s(self):
        return MFTAttribute.TYPES.get(self.type_id, 'Unrecognized')

    def tabulate(self):
        return [['Type ID', '{} ({})'.format(self.type_id, self.type_s)],
                ['Size', self.size],
                ['Non-Resident Flag', self.nr_flag],
                ['Name Length', self.name_length],
                ['Name Offset', self.name_offset],
                ['Flags', bin(self.flags)],
                ['Attribute ID', self.attr_id]]

    def __str__(self):
        return tabulate(self.tabulate(),
                        headers=['Field', 'Value'])

    def __repr__(self):
        return self.__str__()


class MFTEntry(object):
    def __init__(self, data, parent):
        self.data = data
        self.parent = parent

        self.sig = data[0:4]
        self.offset_fixup = struct.unpack('<H', data[4:6])[0]
        self.fixup_entry_count = struct.unpack('<H', data[6:8])[0]
        self.lsn = struct.unpack('<Q', data[8:16])[0]
        self.seq = struct.unpack('<H', data[16:18])[0]
        self.link_count = struct.unpack('<H', data[18:20])[0]
        self.attr_offset = struct.unpack('<H', data[20:22])[0]
        self.flags = struct.unpack('<H', data[22:24])[0]
        self.used_size = struct.unpack('<I', data[24:28])[0]
        self.alloc_size = struct.unpack('<I', data[28:32])[0]
        self.base_ref = struct.unpack('<Q', data[32:40])[0]
        self.next_attr_id = struct.unpack('<H', data[40:42])[0]
        self._attrs = None

    @property
    def attributes(self):
        if self._attrs is None:
            self._attrs = []
            offset = self.attr_offset
            while self.data[offset:offset+4] != b'\xFF' * 4:
                attr = MFTAttribute(self.data, offset)
                self._attrs.append(attr)
                offset += attr.size

        return self._attrs

    def tabulate(self):
        return [['Signature', '{}({})'.format(self.sig.decode(), self.sig.hex())],
                ['Offset to Fixup', self.offset_fixup],
                ['Entry Count in Fixup Array', self.fixup_entry_count],
                ['$LogFile Sequence Number', self.lsn],
                ['Sequence Number', self.seq],
                ['Link Count', self.link_count],
                ['Attribute Offset', self.attr_offset],
                ['Flags', bin(self.flags)],
                ['Used Size of MFT Entry', self.used_size],
                ['Allocated Size of MFT Entry', self.alloc_size],
                ['File Reference to Base Record', self.base_ref],
                ['Next Attribute ID', self.next_attr_id],
                ['#attributes', len(self.attributes)], ]

    def __str__(self):
        return tabulate(self.tabulate(),
                        headers=['Field', 'Value'])

    def __repr__(self):
        return self.__str__()


class File(object):
    pass


class MFT(File):
    pass


class NTFS(Entity):
    def __init__(self, dv, sector0, parent):
        self.boot_sector = BootSector(sector0)

        Entity.__init__(self, dv.disk, dv.begin, dv.size,
                        self.boot_sector.bytes_per_sector,
                        -1, parent)

        self.sectors = DataUnits(self, self.sector_size, self.sector_count)

        bs = self.boot_sector
        cluster_size = self.sector_size * bs.sectors_per_cluster
        cluster_count = bs.total_sectors // bs.sectors_per_cluster
        self.clusters = DataUnits(self, cluster_size, cluster_count)

        self.mft = MFTEntry(self.clusters[self.boot_sector.mft_cluster_number], self)


def try_get(disk, sector0, parent):
    if sector0[3:11] == NTFS_SIGNATURE:
        return NTFS(disk, sector0, parent)
