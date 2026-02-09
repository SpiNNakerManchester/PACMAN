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
from typing import Generic, Optional, Type, TypeVar, cast

from spinn_utilities.overrides import overrides

from pacman.exceptions import (
    PacmanConfigurationException, PartitionMissingEdgesException,
    SysRAMEdgeSizeException)
from pacman.model.graphs.machine import AbstractSysRAMPartition
from pacman.model.graphs import AbstractSingleSourcePartition
from pacman.model.graphs.machine import SysRAMMachineEdge

from .machine_vertex import MachineVertex

#: :meta private:
V = TypeVar("V", bound=MachineVertex)
#: :meta private:
E = TypeVar("E", bound=SysRAMMachineEdge)


class ConstantSysRAMMachinePartition(
        AbstractSingleSourcePartition[V, E], Generic[V, E],
        AbstractSysRAMPartition):
    """
    An SysRAM partition that uses a fixed amount of memory. The edges in
    the partition must agree on how much memory is required.
    """

    __slots__ = (
        # The system RAM base address for this partition.
        "_sysram_base_address",
        # The system RAM size of every edge or None if no edge added.
        "_sysram_size")

    def __init__(self, identifier: str, pre_vertex: V):
        """
        :param identifier: The identifier of the partition
        :param pre_vertex: The vertex at the start of all the edges
        """
        super().__init__(
            pre_vertex, identifier,
            allowed_edge_types=cast(Type[E], SysRAMMachineEdge))
        self._sysram_size: Optional[int] = None
        self._sysram_base_address: Optional[int] = None

    @overrides(AbstractSingleSourcePartition.add_edge)
    def add_edge(self, edge: E) -> None:
        if self._sysram_size is None:
            self._sysram_size = edge.sysram_size
        elif self._sysram_size != edge.sysram_size:
            raise SysRAMEdgeSizeException(
                f"The edges within the constant system RAM partition {self} "
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
        if self._sysram_size is None:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        return self._sysram_size

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
        for edge in self.edges:
            cast(E, edge).sysram_base_address = new_value

    @overrides(AbstractSysRAMPartition.get_sysram_base_address_for)
    def get_sysram_base_address_for(self, vertex: MachineVertex) -> int:
        if self._sysram_base_address is None:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        return self._sysram_base_address

    @overrides(AbstractSysRAMPartition.get_sysram_size_of_region_for)
    def get_sysram_size_of_region_for(self, vertex: MachineVertex) -> int:
        if self._sysram_size is None:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        return self._sysram_size
