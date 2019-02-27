from . import fat
from . import ntfs


def get_filesystem(disk):
    disk.seek(0)
    sector0 = disk.read(512)
    return ([fs.try_get(disk, sector0) for fs in [fat, ntfs]] + [None])[0]
