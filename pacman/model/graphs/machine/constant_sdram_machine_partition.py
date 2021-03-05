# Copyright (c) 2019-2020 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from pacman.model.graphs.machine import AbstractSDRAMPartition
from pacman.model.graphs import AbstractSingleSourcePartition
from spinn_utilities.overrides import overrides
from pacman.exceptions import (
    PacmanConfigurationException, PartitionMissingEdgesException,
    SDRAMEdgeSizeException)
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import SDRAMMachineEdge


class ConstantSDRAMMachinePartition(
        AbstractSingleSourcePartition, AbstractSDRAMPartition):
    """ An SDRAM partition that uses a fixed amount of memory. The edges in\
        the partition must agree on how much memory is required.
    """

    __slots__ = [
        # The sdram base address for this partition.
        "_sdram_base_address",
        # The sdram size of every edge or None if no edge added.
        "_sdram_size",
    ]

    MISSING_EDGE_ERROR_MESSAGE = "Partition {} has no edges"

    def __init__(self, identifier, pre_vertex, label):
        super().__init__(
            pre_vertex, identifier, allowed_edge_types=SDRAMMachineEdge,
            constraints=None, label=label, traffic_weight=1,
            class_name="ConstantSDRAMMachinePartition")
        self._sdram_size = None
        self._sdram_base_address = None

    @property
    @overrides(AbstractSDRAMPartition.traffic_type)
    def traffic_type(self):
        return EdgeTrafficType.SDRAM

    @overrides(AbstractSingleSourcePartition.add_edge)
    def add_edge(self, edge, graph_code):
        if self._sdram_size is None:
            self._sdram_size = edge.sdram_size
        elif self._sdram_size != edge.sdram_size:
            raise SDRAMEdgeSizeException(
                "The edges within the constant sdram partition {} have "
                "inconsistent memory size requests.".format(self))
        if self._sdram_base_address is None:
            super().add_edge(edge, graph_code)
        else:
            raise PacmanConfigurationException(
                "Illegal attempt to add an edge after sdram_base_address set")

    @overrides(AbstractSDRAMPartition.total_sdram_requirements)
    def total_sdram_requirements(self):
        if self._sdram_size is None:
            raise PartitionMissingEdgesException(
                self.MISSING_EDGE_ERROR_MESSAGE.format(self))
        return self._sdram_size

    @property
    def sdram_base_address(self):
        if self._sdram_size is None:
            raise PartitionMissingEdgesException(
                self.MISSING_EDGE_ERROR_MESSAGE.format(self))
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        if len(self.edges) == 0:
            raise PartitionMissingEdgesException(
                self.MISSING_EDGE_ERROR_MESSAGE.format(self))
        self._sdram_base_address = new_value
        for edge in self.edges:
            edge.sdram_base_address = self._sdram_base_address

    @overrides(AbstractSDRAMPartition.get_sdram_base_address_for)
    def get_sdram_base_address_for(self, vertex):
        return self._sdram_base_address

    @overrides(AbstractSDRAMPartition.get_sdram_size_of_region_for)
    def get_sdram_size_of_region_for(self, vertex):
        if len(self._edges) == 0:
            return 0
        return self._edges.peek().sdram_size

    @overrides(AbstractSingleSourcePartition.clone_without_edges)
    def clone_without_edges(self):
        """
        :rtype: ConstantSDRAMMachinePartition
        """
        return ConstantSDRAMMachinePartition(
            self._identifier, self._pre_vertex, self._label)
