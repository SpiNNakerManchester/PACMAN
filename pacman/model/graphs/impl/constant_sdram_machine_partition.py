from pacman.exceptions import SDRAMEdgeSizeException
from pacman.model.graphs.abstract_sdram_partition import AbstractSDRAMPartition
from pacman.model.graphs.\
    abstract_traffic_type_secure_outgoing_partition import \
    AbstractTrafficTypeSecureOutgoingPartition
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine.machine_sdram_edge import SDRAMMachineEdge
from spinn_utilities.overrides import overrides


class ConstantSDRAMMachinePartition(
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

    @property
    def pre_vertex(self):
        return self._pre_vertex

    @overrides(AbstractSDRAMPartition.total_sdram_requirements)
    def total_sdram_requirements(self):
        expected_size = self.edges.peek().sdram_size
        for edge in self.edges:
            if edge.sdram_size != expected_size:
                raise SDRAMEdgeSizeException(
                    "The edges within the constant sdram partition {} have "
                    "inconsistent memory size requests. ")
        return expected_size

    @property
    def sdram_base_address(self):
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        self._sdram_base_address = new_value
        for edge in self.edges:
            edge.sdram_base_address = self._sdram_base_address
