from tabulate import tabulate

import struct


class BootSector(object):
    SIGNATURE = b'NTFS    '

    def __init__(self, sector0):
        self.data = sector0[0:0x200]
        self.jmp = sector0[0:3]
        self.signature = sector0[3:11]
        assert self.signature == BootSector.SIGNATURE
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
