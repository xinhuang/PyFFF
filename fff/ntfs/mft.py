from typing import Optional

from .file import File
from .mft_entry import MFTEntry


class MFT(File):
    def __init__(self, filesystem, data: bytes):
        mft_entry = MFTEntry(data, filesystem, 0)
        File.__init__(self, mft_entry, filesystem)

        self.mft_entries = {0: self.mft_entry}

    def find(self, name: Optional[str] = None, inode: Optional[int] = None) -> Optional[File]:
        bs = self.fs.cluster_size
        data = b''.join(self.read2(count=self.size))
        if name is not None:
            for i in range(1, len(data) // bs):
                e = MFTEntry(data[i*bs:(i+1)*bs], self.fs, i)
                self.mft_entries[i] = e
                f = File(e, self.fs)
                if f.name == name:
                    return f
        elif inode is not None:
            if inode >= len(data) // bs:
                raise Exception('inode too large')
            e = MFTEntry(data[inode*bs:(inode+1)*bs], self.fs, inode)
            self.mft_entries[inode] = e
            return File(e, self.fs)
        return None
