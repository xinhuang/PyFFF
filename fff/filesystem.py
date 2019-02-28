from . import fat
from . import ntfs


FILESYSTEMS = [ntfs, fat]


def get_filesystem(disk_view, parent):
    disk_view.seek(0)
    sector0 = disk_view.read(512)
    candidates = (fs.try_get(disk_view, sector0, parent) for fs in FILESYSTEMS)
    return next((c for c in candidates if c is not None))
