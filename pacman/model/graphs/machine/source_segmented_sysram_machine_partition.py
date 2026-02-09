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
from typing import Collection, Optional
from spinn_utilities.overrides import overrides
from pacman.exceptions import (
    PacmanConfigurationException, PartitionMissingEdgesException,
    PacmanValueError)
from pacman.model.graphs import AbstractMultiplePartition
from pacman.model.graphs.machine import (
    AbstractSysRAMPartition, SysRAMMachineEdge, MachineVertex)


class SourceSegmentedSysRAMMachinePartition(
        AbstractMultiplePartition[MachineVertex, SysRAMMachineEdge],
        AbstractSysRAMPartition):
    """
    A System RAM partition that gives each edge its own slice of memory from a
    contiguous block. The edges all have the same destination vertex.
    """
    __slots__ = ("_sysram_base_address", )

    def __init__(
            self, identifier: str, pre_vertices: Collection[MachineVertex]):
        """
        :param identifier: The identifier of the partition
        :param pre_vertices:
            The vertices that an edge in this partition may originate at
        """
        super().__init__(
            pre_vertices, identifier, allowed_edge_types=SysRAMMachineEdge)
        self._sysram_base_address: Optional[int] = None

    def total_sysram_requirements(self) -> int:
        """
        :returns: The total of the system RAM size of each edge.
        """
        return sum(edge.sysram_size for edge in self.edges)

    @property
    def sysram_base_address(self) -> int:
        """
        The start of the system RAM block reserved on Chip
        """
        if self._sysram_base_address is None:
            raise PacmanConfigurationException(
                "SysRAM base address not yet set")
        return self._sysram_base_address

    @sysram_base_address.setter
    def sysram_base_address(self, new_value: int) -> None:
        if len(self.pre_vertices) != len(self.edges):
            raise PartitionMissingEdgesException(
                f"There are {len(self.pre_vertices)} pre vertices "
                f"but only {len(self.edges)} edges")

        self._sysram_base_address = new_value

        for pre_vertex in self._pre_vertices:
            # allocate for the pre_vertex
            edge = self._pre_vertices[pre_vertex].peek()
            edge.sysram_base_address = new_value
            new_value += edge.sdram_size

    @overrides(AbstractMultiplePartition.add_edge)
    def add_edge(self, edge: SysRAMMachineEdge) -> None:
        # check
        if len(self._destinations):
            if edge.post_vertex not in self._destinations:
                raise PacmanConfigurationException(
                    f"The {self.__class__.__name__} can only support "
                    "1 destination vertex")
        try:
            if len(self._pre_vertices[edge.pre_vertex]) != 0:
                raise PacmanConfigurationException(
                    f"The {self.__class__.__name__} only supports 1 edge from "
                    "a given pre vertex.")
        except KeyError as ex:
            raise PacmanConfigurationException(
                "Edge pre_vertex is not a Partition. pre vertex") from ex
        # add
        super().add_edge(edge)

    def is_sysram_base_address_defined(self, vertex: MachineVertex) -> bool:
        """
        Do we have a base address for the given vertex? If the edge does not
        connect to the vertex, this is an error.

        :returns: True if the base address for the given vertex is known
        """
        if self._sysram_base_address is None:
            return False
        return (
            self._pre_vertices[vertex].peek().sysram_base_address is not None)

    @overrides(AbstractSysRAMPartition.get_sysram_base_address_for)
    def get_sysram_base_address_for(self, vertex: MachineVertex) -> int:
        if self._sysram_base_address is None:
            raise PacmanValueError("no base address set for SysRAM partition")
        if vertex in self._pre_vertices:
            addr = self._pre_vertices[vertex].peek().sysram_base_address
            if addr is None:
                raise PacmanValueError(
                    f"no base address set for vertex {vertex.label}")
            return addr
        else:
            return self._sysram_base_address

    @overrides(AbstractSysRAMPartition.get_sysram_size_of_region_for)
    def get_sysram_size_of_region_for(self, vertex: MachineVertex) -> int:
        if vertex in self._pre_vertices:
            return self._pre_vertices[vertex].peek().sysram_size
        else:
            return self.total_sysram_requirements()
