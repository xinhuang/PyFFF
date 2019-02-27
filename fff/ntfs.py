import struct


class NTFS(object):
    def __init__(self, disk, sector0):
        pass


def try_get(disk, sector0):
    if sector0[3:11] == b'NTFS    ':
        return NTFS(disk, sector0)
