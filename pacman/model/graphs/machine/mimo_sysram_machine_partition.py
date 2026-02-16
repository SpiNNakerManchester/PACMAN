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
from typing import Generic, Optional, Type, cast, Dict

from spinn_utilities.overrides import overrides
from spinn_utilities.ordered_set import OrderedSet

from pacman.exceptions import (
    PacmanConfigurationException, PartitionMissingEdgesException,
    SysRAMEdgeSizeException)
from pacman.model.graphs.machine import AbstractSysRAMPartition
from pacman.model.graphs import AbstractMultiplePartition
from pacman.model.graphs.machine import SysRAMMachineEdge

from .machine_vertex import MachineVertex


class MimoSysRAMMachinePartition(
        AbstractMultiplePartition[MachineVertex, SysRAMMachineEdge],
        Generic[MachineVertex, SysRAMMachineEdge],
        AbstractSysRAMPartition):
    """
    A SysRAM partition that has multiple inputs and multiple outputs, and all
    sources have edges to all destinations.  All sources share SysRAM access,
    and each target then has its own slice of that shared SysRAM access. Thus,
    the size of the SysRAM needed by each edge that targets a particular
    destination must be the same.
    """

    __slots__ = (
        # The system RAM base address for this partition.
        "_sysram_base_address",
        # The system RAM size for each destination vertex.
        "_sysram_size",
        # The system RAM address for each destination vertex.
        "_sysram_address_by_destination")

    def __init__(self, pre_vertices: OrderedSet[MachineVertex],
                 identifier: str):
        """
        :param pre_vertices: The vertices which send through this partition
        :param identifier: The identifier of the partition
        """
        super().__init__(
            pre_vertices, identifier,
            allowed_edge_types=SysRAMMachineEdge)
        self._sysram_size: Dict[MachineVertex, int] = dict()
        self._sysram_base_address: Optional[int] = None
        self._sysram_address_by_destination: Dict[MachineVertex, int] = dict()

    @overrides(AbstractMultiplePartition.add_edge)
    def add_edge(self, edge: SysRAMMachineEdge) -> None:
        if edge.post_vertex not in self._sysram_size:
            self._sysram_size[edge.post_vertex] = edge.sysram_size
        elif self._sysram_size[edge.post_vertex] != edge.sysram_size:
            raise SysRAMEdgeSizeException(
                f"The edges within the MIMO system RAM partition {self} "
                "have inconsistent memory size requests.")
        if self._sysram_base_address is None:
            super().add_edge(edge)
        else:
            raise PacmanConfigurationException(
                "Illegal attempt to add an edge after sysram_base_address set")

    def __missing_edge_msg(self) -> str:
        return f"Partition {self} has no edges"

    @overrides(AbstractSysRAMPartition.total_sysram_requirements)
    def total_sysram_requirements(self) -> int:
        if len(self.edges) == 0:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        return sum(self._sysram_size.values())

    @property
    @overrides(AbstractSysRAMPartition.sysram_base_address)
    def sysram_base_address(self) -> int:
        if self._sysram_base_address is None:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        return self._sysram_base_address

    @sysram_base_address.setter
    def sysram_base_address(self, new_value: int) -> None:
        if len(self.edges) == 0:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        self._sysram_base_address = new_value
        for destination in self._sysram_size:
            self._sysram_address_by_destination[destination] = new_value
            new_value += self._sysram_size[destination]
        for edge in self.edges:
            cast(SysRAMMachineEdge, edge).sysram_base_address = \
                self._sysram_address_by_destination[edge.post_vertex]

    @overrides(AbstractSysRAMPartition.get_sysram_base_address_for)
    def get_sysram_base_address_for(self, vertex: MachineVertex) -> int:
        if self._sysram_base_address is None:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        # This is a destination vertex, so return the address for it.
        if vertex in self._sysram_address_by_destination:
            return self._sysram_address_by_destination[vertex]

        # Otherwise, this is a source vertex, so return the base address for
        # the whole partition.
        return self._sysram_base_address

    @overrides(AbstractSysRAMPartition.get_sysram_size_of_region_for)
    def get_sysram_size_of_region_for(self, vertex: MachineVertex) -> int:
        if len(self.edges) == 0:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        if vertex in self._sysram_size:
            return self._sysram_size[vertex]
        return self.total_sysram_requirements()
