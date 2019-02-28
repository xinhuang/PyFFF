from . import fat
from . import ntfs


FILESYSTEMS = [ntfs, fat]


def get_filesystem(disk):
    disk.seek(0)
    sector0 = disk.read(512)
    candidates = (fs.try_get(disk, sector0) for fs in FILESYSTEMS)
    return next((c for c in candidates if c is not None))
