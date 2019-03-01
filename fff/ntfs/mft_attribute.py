from tabulate import tabulate

import struct


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
