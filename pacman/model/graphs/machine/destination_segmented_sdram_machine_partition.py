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

from spinn_utilities.overrides import overrides
from pacman.exceptions import (
    PacmanConfigurationException,  PartitionMissingEdgesException,
    PacmanValueError)
from pacman.model.graphs import AbstractSingleSourcePartition
from pacman.model.graphs.machine import (
    AbstractSDRAMPartition, SDRAMMachineEdge)


class DestinationSegmentedSDRAMMachinePartition(
        AbstractSingleSourcePartition, AbstractSDRAMPartition):
    """ An SDRAM partition that gives each edge its own slice of memory from a\
        contiguous block. The edges all have the same source vertex.
    """
    __slots__ = [
        # The sdram base address for this partition.
        "_sdram_base_address",
    ]

    def __init__(self, identifier, pre_vertex):
        super().__init__(
            pre_vertex=pre_vertex, identifier=identifier,
            allowed_edge_types=SDRAMMachineEdge)
        self._sdram_base_address = None

    @overrides(AbstractSDRAMPartition.total_sdram_requirements)
    def total_sdram_requirements(self):
        return sum(edge.sdram_size for edge in self.edges)

    @property
    def sdram_base_address(self):
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        if len(self.edges) == 0:
            raise PartitionMissingEdgesException(
                "Partition {} has no edges".format(self))
        self._sdram_base_address = new_value
        for edge in self.edges:
            edge.sdram_base_address = new_value
            new_value += edge.sdram_size

    @overrides(AbstractSingleSourcePartition.add_edge)
    def add_edge(self, edge):
        if self._sdram_base_address is not None:
            raise PacmanConfigurationException(
                "Illegal attempt to add an edge after sdram_base_address set")

        # safety check
        if self._pre_vertex != edge.pre_vertex:
            raise PacmanConfigurationException(
                "The destination segmented SDRAM partition only accepts "
                "1 pre-vertex")

        # add
        super().add_edge(edge)

    @overrides(AbstractSDRAMPartition.get_sdram_base_address_for)
    def get_sdram_base_address_for(self, vertex):
        if self._pre_vertex == vertex:
            return self._sdram_base_address
        for edge in self._edges:
            if edge.post_vertex == vertex:
                return edge.sdram_base_address
        raise PacmanValueError(f"Vertex {vertex} is not in this partition")

    @overrides(AbstractSDRAMPartition.get_sdram_size_of_region_for)
    def get_sdram_size_of_region_for(self, vertex):
        if self._pre_vertex == vertex:
            return self.total_sdram_requirements()
        for edge in self._edges:
            if edge.post_vertex == vertex:
                return edge.sdram_size
        raise PacmanValueError(f"Vertex {vertex} is not in this partition")
