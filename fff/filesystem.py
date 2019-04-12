from . import fat
from . import ntfs


FILESYSTEMS = [ntfs, fat]


def get_filesystem(disk_view, parent):
    sector0 = disk_view.read(512, offset=0)
    candidates = (fs.try_get(disk_view, sector0, parent) for fs in FILESYSTEMS)
    return next((c for c in candidates if c is not None))
