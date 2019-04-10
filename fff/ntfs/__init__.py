from .mft_entry import *
from .boot_sector import *
from .mft_attr import *
from .mft import *
from .file import *
from .ntfs import *

from typing import Optional


def try_get(disk: DiskView, sector0: bytes, parent) -> Optional[NTFS]:
    if sector0[3: 11] == BootSector.SIGNATURE:
        return NTFS(disk, sector0, parent)
    else:
        return None
