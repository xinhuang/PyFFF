from .mft_attr import AttrHeader, AttributeList, MFTAttr
from .file_ref import FileRef
from ..disk_view import DiskView

from tabulate import tabulate
from hexdump import hexdump

import struct
from typing import List, Union, Optional, TYPE_CHECKING, cast, Dict

if TYPE_CHECKING:
    from .mft import MFT


class MFTEntry(object):
    def __init__(self, data, dv: DiskView, inode: int, mft: 'Optional[MFT]' = None):
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
        self.base_ref = FileRef(data[32:40])
        self.next_attr_id = struct.unpack('<H', data[40:42])[0]

        if not self.in_use:
            return

        headers: List[AttrHeader] = []
        offset = self.attr_offset
        offmap: Dict[AttrHeader, int] = {}
        while self.data[offset:offset+4] != b'\xFF' * 4:
            h = AttrHeader(self.data, offset)
            headers.append(h)
            offmap[h] = offset
            offset += h.size

        self._attrs: List[MFTAttr] = []
        headers = sorted(headers, key=lambda a: a.type_id)
        for h in headers:
            rdata: Optional[bytes] = None
            if not h.non_resident:
                of = offmap[h] + h.attr_offset
                rdata = data[of:of+h.attr_length]

            nrdata: Optional[bytes] = None
            if h.type_id != 0x080 and h.non_resident:
                d = []
                for dr in h.vcn.drs:
                    assert dr.offset
                    d.append(dv.clusters[dr.offset:dr.offset+dr.length])
                nrdata = b''.join(d)
            attr = h.create(self, rdata, nrdata)
            self._attrs.append(attr)

            if h.type_id == 0x020:
                attr = cast(AttributeList, attr)
                inodes = set([e.file_ref.inode for e in attr.entries])
                inodes.discard(inode)    # don't recursive into itself
                assert mft
                entries = list(map(lambda inode: mft.find(inode=inode), inodes))  # type: ignore
                for e in entries:
                    assert e
                    self._attrs += e._attrs

    def attrs(self, type_id: Union[int, str, None] = None, name: Optional[str] = None) -> List[MFTAttr]:
        r = self._attrs
        if isinstance(type_id, str):
            r = [a for a in self._attrs if a.header.type_s == type_id]
        elif isinstance(type_id, int):
            r = [a for a in self._attrs if a.header.type_id == type_id]
        if name is not None:
            r = [a for a in r if a.header.name == name]
        return list(r)

    def attr(self, *args, **kwargs) -> Optional[MFTAttr]:
        attrs = self.attrs(*args, **kwargs)
        return attrs[0] if attrs else None

    @property
    def is_file(self):
        return self.flags == 0x01

    @property
    def is_dir(self):
        return self.flags & 2 != 0

    @property
    def in_use(self):
        return self.flags != 0

    @property
    def flags_s(self):
        FLAGS = {
            0x00: 'Not in use',
            0x01: 'In use',
            0x02: 'Directory',
            0x03: 'Directory in use',
        }
        return FLAGS.get(self.flags)

    def tabulate(self):
        return [['inode', self.inode],
                ['Signature', '{}({})'.format(self.sig.decode(), self.sig.hex())],
                ['Offset to Fixup', self.offset_fixup],
                ['Entry Count in Fixup Array', self.fixup_entry_count],
                ['$LogFile Sequence Number', self.lsn],
                ['Sequence Number', self.seq],
                ['Link Count', self.link_count],
                ['Attribute Offset', self.attr_offset],
                ['Flags', '{} ({})'.format(self.flags_s, hex(self.flags))],
                ['Used Size of MFT Entry', self.used_size],
                ['Allocated Size of MFT Entry', self.alloc_size],
                ['Base Record', self.base_ref.inode],
                ['Next Attribute ID', self.next_attr_id],
                ['#attributes', len(self._attrs)], ]

    def __str__(self):
        return tabulate(self.tabulate())

    def __repr__(self):
        return self.__str__()
