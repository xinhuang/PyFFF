from .file import File
from .mft_entry import MFTEntry
from .mft_attr import FileName

from typing import cast, Optional


class MFT(File):
    def __init__(self, filesystem, data: bytes):
        mft_entry = MFTEntry(data, filesystem.dv, 0)
        File.__init__(self, mft_entry, filesystem)

        self.entries = {0: self.mft_entry}
        self._data = None

        mft_clusters: int = self.size // filesystem.cluster_size
        self.entry_total: int = mft_clusters // filesystem.boot_sector.cluster_per_file_record_segment

    @property
    def data(self):
        if self._data is None:
            self._data = b''.join(self.read(count=self.size))
        return self._data

    def find(self, name: Optional[str] = None, inode: Optional[int] = None) -> Optional[MFTEntry]:
        bs = self.fs.cluster_size
        data = self.data
        if name is not None:
            for i in range(1, len(data) // bs):
                e = MFTEntry(data[i*bs:(i+1)*bs], self.fs, i, self)
                self.entries[i] = e
                for fn in e.attrs(type_id='$FILE_NAME'):
                    fn = cast(FileName, fn)
                    if fn.filename == name:
                        return e
        elif inode is not None:
            if inode >= len(data) // bs:
                raise Exception('inode too large')
            if inode in self.entries:
                return self.entries[inode]
            else:
                e = MFTEntry(data[inode*bs:(inode+1)*bs], self.fs, inode, self)
                self.entries[inode] = e
                return e
        return None
