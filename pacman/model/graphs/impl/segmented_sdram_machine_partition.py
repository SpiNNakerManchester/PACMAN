from pacman.model.graphs.abstract_sdram_partition import AbstractSDRAMPartition
from pacman.model.graphs.abstract_traffic_type_secure_outgoing_partition import \
    AbstractTrafficTypeSecureOutgoingPartition
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine.machine_sdram_edge import SDRAMMachineEdge
from pacman.utilities import constants
from spinn_utilities.overrides import overrides


class SegmentedSDRAMMachinePartition(
        AbstractTrafficTypeSecureOutgoingPartition, AbstractSDRAMPartition):

    __slots__ = [
        "_sdram_base_address",
        "_pre_vertex"
    ]

    def __init__(self, identifier, pre_vertex, label):
        AbstractTrafficTypeSecureOutgoingPartition.__init__(
            self,  identifier=identifier,
            allowed_edge_types=SDRAMMachineEdge,
            label=label, traffic_type=EdgeTrafficType.SDRAM)
        AbstractSDRAMPartition.__init__(self)
        self._sdram_base_address = None
        self._pre_vertex = pre_vertex

    @overrides(AbstractSDRAMPartition.total_sdram_requirements)
    def total_sdram_requirements(self):
        total = 0
        for edge in self.edges:
            total += edge.sdram_size
        return total

    @property
    def pre_vertex(self):
        return self._pre_vertex

    @property
    def sdram_base_address(self):
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        self._sdram_base_address = new_value
        for edge in self.edges:
            edge.sdram_base_address = (
                new_value + (edge.pre_vertex.input_slice.lo_atom *
                             constants.BYTE_TO_WORD_MULTIPLIER))