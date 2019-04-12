from . import mft_attr
from ..disk_view import DiskView

from tabulate import tabulate

import struct


class MFTEntry(object):
    def __init__(self, data, dv: DiskView, inode: int):
        self.data = data

        self.inode = inode

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
    def attrs(self):
        if self._attrs is None:
            self._attrs = []
            offset = self.attr_offset
            while self.data[offset:offset+4] != b'\xFF' * 4:
                attr = mft_attr.create(self.data, offset)
                self._attrs.append(attr)
                offset += attr.size

        return self._attrs

    def tabulate(self):
        return [['inode', self.inode],
                ['Signature', '{}({})'.format(self.sig.decode(), self.sig.hex())],
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
                ['#attributes', len(self.attrs)], ]

    def __str__(self):
        return tabulate(self.tabulate(),
                        headers=['Field', 'Value'])

    def __repr__(self):
        return self.__str__()
