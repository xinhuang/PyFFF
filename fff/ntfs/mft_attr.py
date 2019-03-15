from tabulate import tabulate

import struct
from typing import List, Tuple, Any

# http://www.cse.scu.edu/~tschwarz/coen252_07Fall/Lectures/NTFS.html
TYPES = {
    0x010: '$StandardInformation',
    0x020: '$ATTRIBUTE_LIST',
    0x030: '$FILE_NAME',
    0x040: '$VOLUME_VERSION',
    0x050: '$OBJECT_ID',
    0x060: '$VOLUME_NAME',
    0x070: '$VOLUME_INFORMATION',
    0x080: '$DATA',
    0x090: '$INDEX_ROOT',
    0x0A0: '$INDEX_ALLOCATION',
    0x0B0: '$BITMAP',
    0x0C0: '$SYMBOLIC_LINK(NT) | $REPARSE_POINT(2K)',
    0x0D0: '$EA_INFORMATION',
    0x0E0: '$EA',
    0x0F0: '$PROPERTY_SET',
    0x100: '$LOGGED_UTILITY_STREAM',
}


class MFTAttr(object):
    def __init__(self, data: bytes, offset: int, filesystem):
        self.type_id = struct.unpack('<I', data[offset:offset+4])[0]
        self.size = struct.unpack('<I', data[offset+4:offset+8])[0]
        assert offset + self.size <= len(data)
        self.non_resident = bool(data[offset+8])
        self.name_length = data[offset+9]
        self.name_offset = struct.unpack('<H', data[offset+10:offset+12])[0]
        self.flags = struct.unpack('<H', data[offset+12:offset+14])[0]
        self.attr_id = struct.unpack('<H', data[offset+14:offset+16])[0]

        self.data = data[offset:offset+self.size]

    @property
    def type_s(self):
        name = TYPES.get(self.type_id, 'Unrecognized')
        return name if isinstance(name, str) else name.NAME

    def tabulate(self):
        return [['Type ID', '{} ({})'.format(self.type_id, self.type_s)],
                ['Size', self.size],
                ['Non-Resident Flag', self.non_resident],
                ['Name Length', self.name_length],
                ['Name Offset', self.name_offset],
                ['Flags', bin(self.flags)],
                ['Attribute ID', self.attr_id]]

    def __str__(self):
        return tabulate(self.tabulate(),
                        headers=['Field', 'Value'])

    def __repr__(self):
        return self.__str__()


def create(data, offset, filesystem):
    type_id = struct.unpack('<I', data[offset:offset+4])[0]
    ctor = TYPES.get(type_id)

    if isinstance(ctor, str):
        return MFTAttr(data, offset, filesystem)
    else:
        return ctor(data, offset, filesystem)


def MFTAttribute(type_id, name):
    def decorator(cls):
        cls.NAME = name
        TYPES[type_id] = cls

        def wrapper(*args, **kwargs):
            return cls(*args, **kwargs)
        return wrapper
    return decorator


DOS_PERM = {
    0x0001: 'Read-Only',
    0x0002: 'Hidden',
    0x0004: 'System',
    0x0020: 'Archive',
    0x0040: 'Device',
    0x0080: 'Normal',
    0x0100: 'Temporary',
    0x0200: 'Sparse File',
    0x0400: 'Reparse Point',
    0x0800: 'Compressed',
    0x1000: 'Offline',
    0x2000: 'Not Content Indexed',
    0x4000: 'Encrypted',
}


@MFTAttribute(0x010, '$STANDARD_INFORMATION')
class StandardInformation(MFTAttr):

    def __init__(self, data: bytes, offset: int, filesystem):
        super().__init__(data, offset, filesystem)

        # TODO: Non-resident flag
        assert not self.non_resident

        offset += 0x18
        self.ctime = struct.unpack('<Q', data[offset:offset+8])[0]  # File creation
        self.atime = struct.unpack('<Q', data[offset+8:offset+16])[0]  # File altered
        self.mtime = struct.unpack('<Q', data[offset+16:offset+24])[0]  # MFT changed
        self.rtime = struct.unpack('<Q', data[offset+24:offset+32])[0]  # File read
        self.perm = struct.unpack('<I', data[offset+32:offset+36])[0]
        self.max_ver = struct.unpack('<I', data[offset+36:offset+40])[0]
        self.ver = struct.unpack('<I', data[offset+40:offset+44])[0]
        self.class_id = struct.unpack('<I', data[offset+44:offset+48])[0]
        if self.size > 48:
            self.owner_id = struct.unpack('<I', data[offset+48:offset+52])[0]
            self.security_id = struct.unpack('<I', data[offset+52:offset+56])[0]
            self.quota_charged = struct.unpack('<Q', data[offset+56:offset+64])[0]
            self.usn = struct.unpack('<Q', data[offset+64:offset+72])[0]  # Update Sequence Number
        else:
            self.owner_id = None
            self.security_id = None
            self.quota_charged = None
            self.usn = None

    @property
    def perm_s(self) -> str:
        s = hex(self.perm) + ' ('
        for k in sorted(DOS_PERM.keys()):
            if self.perm & k:
                s += DOS_PERM[k] + ', '
        s = s.rstrip(', ') + ')'
        return s

    def tabulate(self) -> List[Tuple[str, Any]]:
        return super().tabulate() + [
            ['Created', self.ctime],
            ['Modified', self.atime],
            ['MFT Modified', self.mtime],
            ['Accessed', self.rtime],
            ['DOS Permission', self.perm_s],
            ['Max Version', self.max_ver],
            ['Version', self.ver],
            ['Class ID', self.class_id],
            ['Owner ID', self.owner_id],
            ['Security ID', self.security_id],
            ['Quota Charged', self.quota_charged],
            ['Update Sequence Number', self.usn], ]


NAMESPACE = {
    0: 'POSIX',
    1: 'Win32',
    2: 'DOS',
    3: 'Win32 & DOS',
}

FLAGS = {
    **DOS_PERM,
    0x10000000: 'Directory (copy from corresponding bit in MFT record)',
    0x20000000: 'Index View (copy from corresponding bit in MFT record)',
}


@MFTAttribute(0x030, '$FILE_NAME')
class FileName(MFTAttr):
    def __init__(self, data: bytes, offset: int, filesystem):
        super().__init__(data, offset, filesystem)

        assert not self.non_resident

        offset += 0x18
        self.parent_dir = struct.unpack('<Q', data[offset:offset+8])[0]
        self.ctime = struct.unpack('<Q', data[offset+8:offset+16])[0]  # File creation
        self.atime = struct.unpack('<Q', data[offset+16:offset+24])[0]  # File altered
        self.mtime = struct.unpack('<Q', data[offset+24:offset+32])[0]  # MFT changed
        self.rtime = struct.unpack('<Q', data[offset+32:offset+40])[0]  # File read
        self.allocated_size = struct.unpack('<Q', data[offset+40:offset+48])[0]
        self.actual_size = struct.unpack('<Q', data[offset+48:offset+56])[0]
        self.flags = struct.unpack('<I', data[offset+56:offset+60])[0]
        self.er = struct.unpack('<I', data[offset+60:offset+64])[0]
        self.name_length = struct.unpack('<B', data[offset+64:offset+65])[0]
        self.namespace = struct.unpack('<B', data[offset+65:offset+66])[0]
        self.filename = data[offset+66:offset+66+self.name_length*2].decode('utf-16')

    @property
    def flags_s(self) -> str:
        s = hex(self.flags) + ' ('
        for k in sorted(FLAGS.keys()):
            if self.flags & k:
                s += FLAGS[k] + ', '
        s = s.rstrip(', ') + ')'
        return s

    @property
    def namespace_s(self) -> str:
        return '{} ({})'.format(self.namespace, NAMESPACE.get(self.namespace, 'Unrecognized'))

    def tabulate(self):
        return super().tabulate() + [
            ['Created', self.ctime],
            ['Modified', self.atime],
            ['MFT Modified', self.mtime],
            ['Accessed', self.rtime],
            ['Allocated Size', self.allocated_size],
            ['Actual Size', self.size],
            ['Flags', self.flags_s],
            ['ER', self.er],
            ['Name Length', self.name_length],
            ['Namespace', self.namespace_s],
            ['File Name', self.filename], ]
