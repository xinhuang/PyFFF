from typing import Optional

from .file import File
from .mft_entry import MFTEntry


class MFT(File):
    def __init__(self, filesystem, data: bytes):
        mft_entry = MFTEntry(data, filesystem.dv, 0)
        File.__init__(self, mft_entry, filesystem)

        self.entries = {0: self.mft_entry}
        self._data = None

    @property
    def data(self):
        if self._data is None:
            self._data = b''.join(self.read2(count=self.size))
        return self._data

    def find(self, name: Optional[str] = None, inode: Optional[int] = None) -> Optional[File]:
        bs = self.fs.cluster_size
        data = self.data
        if name is not None:
            for i in range(1, len(data) // bs):
                e = MFTEntry(data[i*bs:(i+1)*bs], self.fs, i)
                self.entries[i] = e
                f = File(e, self.fs)
                if f.name == name:
                    return f
        elif inode is not None:
            if inode >= len(data) // bs:
                raise Exception('inode too large')
            e = MFTEntry(data[inode*bs:(inode+1)*bs], self.fs, inode)
            self.entries[inode] = e
            return File(e, self.fs)
        return None
