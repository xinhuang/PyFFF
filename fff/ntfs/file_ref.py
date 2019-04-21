from tabulate import tabulate


class FileRef(object):
    def __init__(self, data: bytes):
        assert len(data) == 8
        self.inode = int.from_bytes(data[:5], byteorder='little')
        self.seq = int.from_bytes(data[5:], byteorder='little')

    def tabulate(self):
        return [['inode', self.inode],
                ['Sequence Number', '{} ({})'.format(self.seq, hex(self.seq))], ]

    def __str__(self):
        return '{}, {}'.format(self.inode, self.seq)

    def __repr__(self):
        return self.__str__()
