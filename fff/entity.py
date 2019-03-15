from .disk_view import DiskView
from .data_units import DataUnits

from typing import Optional


class Entity(object):
    def __init__(self):
        pass

    def read(self, offset, size):
        return self.dv.read(offset=offset, size=size)
