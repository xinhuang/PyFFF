from typing import Optional, List, Tuple, cast


class DataRun(object):
    def __init__(self, length: int, offset: Optional[int]):
        self.length = length
        self.offset = offset

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '(offset: {}, length: {})'.format(self.offset, self.length)


class VCN(object):
    def __init__(self, data: Optional[bytes] = None, offset: int = 0):
        self.drs: List[DataRun]
        self.clusters: List[int]
        if data is None:
            self.drs = []
            self.count = 0
            self.clusters = []
        else:
            _, self.drs = parse_data_runs(data, offset)
            self.count = sum([dr.length for dr in self.drs])
            self.clusters = list([c for dr in self.drs for c in self._expand(dr)])

    def _expand(self, dr: DataRun):
        if dr.offset is None:
            return [None] * dr.length
        else:
            return list(range(dr.offset, dr.offset + dr.length))

    def __getitem__(self, index_or_slice):
        return self.clusters[index_or_slice]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '<VCN: {} data runs>'.format(self.count)


def parse_data_runs(data, offset) -> Tuple[int, List[DataRun]]:
    drs: List[DataRun] = []
    while data[offset] != 0:
        header = data[offset]

        nlength = header & 0x0F

        l = int.from_bytes(data[offset+1:offset+1+nlength], byteorder='little')
        noffset = header >> 4
        if noffset == 0:
            o = None
        else:
            o = int.from_bytes(data[offset+1+nlength:offset+1+nlength + noffset],
                               byteorder='little', signed=True)

        drs.append(DataRun(l, o))
        offset += 1 + nlength + noffset

    total_offset = 0
    for i in range(0, len(drs)):
        if drs[i].offset is not None:
            o = cast(int, drs[i].offset)
            total_offset += o
            drs[i].offset = total_offset

    offset += 1
    return offset, drs
