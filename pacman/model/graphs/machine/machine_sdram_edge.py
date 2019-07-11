from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import MachineEdge


class SDRAMMachineEdge(MachineEdge):

    __slots__ = [
        "_sdram_size",
        "_sdram_base_address"

    ]

    def __init__(self, pre_vertex, post_vertex, sdram_size, label):
        MachineEdge.__init__(
            self, pre_vertex, post_vertex, traffic_type=EdgeTrafficType.SDRAM,
            label=label, traffic_weight=1)
        self._sdram_size = sdram_size
        self._sdram_base_address = None

    @property
    def sdram_size(self):
        return self._sdram_size

    @property
    def sdram_base_address(self):
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        self._sdram_base_address = new_value

    def __repr__(self):
        return self._label

    def __str__(self):
        return self.__repr__()
