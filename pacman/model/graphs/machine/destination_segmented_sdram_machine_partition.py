# Copyright (c) 2019 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Optional
from spinn_utilities.overrides import overrides
from pacman.exceptions import (
    PacmanConfigurationException,  PartitionMissingEdgesException,
    PacmanValueError)
from pacman.model.graphs import AbstractSingleSourcePartition
from pacman.model.graphs.machine import (
    AbstractSDRAMPartition, SDRAMMachineEdge, MachineVertex)


class DestinationSegmentedSDRAMMachinePartition(
        AbstractSingleSourcePartition[MachineVertex, SDRAMMachineEdge],
        AbstractSDRAMPartition):
    """
    An SDRAM partition that gives each edge its own slice of memory from a
    contiguous block. The edges all have the same source vertex.
    """
    __slots__ = (
        # The sdram base address for this partition.
        "_sdram_base_address", )

    def __init__(self, identifier: str, pre_vertex: MachineVertex):
        """
        :param identifier: The identifier of the partition
        :param pre_vertex: The vertex at the start of all the edges
        """
        super().__init__(
            pre_vertex=pre_vertex, identifier=identifier,
            allowed_edge_types=SDRAMMachineEdge)
        self._sdram_base_address: Optional[int] = None

    @overrides(AbstractSDRAMPartition.total_sdram_requirements)
    def total_sdram_requirements(self) -> int:
        return sum(edge.sdram_size for edge in self.edges)

    @property
    @overrides(AbstractSDRAMPartition.sdram_base_address)
    def sdram_base_address(self) -> int:
        if self._sdram_base_address is None:
            raise PacmanConfigurationException(
                "SDRAM base address not yet set")
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value: int) -> None:
        if len(self.edges) == 0:
            raise PartitionMissingEdgesException(
                f"Partition {self} has no edges")
        self._sdram_base_address = new_value
        for edge in self.edges:
            edge.sdram_base_address = new_value
            new_value += edge.sdram_size

    @overrides(AbstractSingleSourcePartition.add_edge)
    def add_edge(self, edge: SDRAMMachineEdge) -> None:
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
    def get_sdram_base_address_for(self, vertex: MachineVertex) -> int:
        if self._pre_vertex == vertex:
            if self._sdram_base_address is not None:
                return self._sdram_base_address
        for edge in self._edges:
            if edge.post_vertex == vertex:
                return edge.sdram_base_address
        raise PacmanValueError(f"Vertex {vertex} is not in this partition")

    @overrides(AbstractSDRAMPartition.get_sdram_size_of_region_for)
    def get_sdram_size_of_region_for(self, vertex: MachineVertex) -> int:
        if self._pre_vertex == vertex:
            return self.total_sdram_requirements()
        for edge in self._edges:
            if edge.post_vertex == vertex:
                return edge.sdram_size
        raise PacmanValueError(f"Vertex {vertex} is not in this partition")
