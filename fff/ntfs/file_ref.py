class FileRef(object):
    def __init__(self, data: bytes):
        assert len(data) == 8
        self.inode = int.from_bytes(data[:5], byteorder='little')
        self.seq = int.from_bytes(data[5:], byteorder='little')

    def tabulate(self):
        return [['inode', self.inode],
                ['Sequence Number', '{} ({})'.format(self.seq, hex(self.seq))], ]
