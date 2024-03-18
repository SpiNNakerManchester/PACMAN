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
    SDRAMEdgeSizeException)
from pacman.model.graphs.machine import AbstractSDRAMPartition
from pacman.model.graphs import AbstractSingleSourcePartition
from pacman.model.graphs.machine import SDRAMMachineEdge

from .machine_vertex import MachineVertex

#: :meta private:
V = TypeVar("V", bound=MachineVertex)
#: :meta private:
E = TypeVar("E", bound=SDRAMMachineEdge)


class ConstantSDRAMMachinePartition(
        AbstractSingleSourcePartition[V, E], Generic[V, E],
        AbstractSDRAMPartition):
    """
    An SDRAM partition that uses a fixed amount of memory. The edges in
    the partition must agree on how much memory is required.
    """

    __slots__ = (
        # The sdram base address for this partition.
        "_sdram_base_address",
        # The sdram size of every edge or None if no edge added.
        "_sdram_size")

    def __init__(self, identifier: str, pre_vertex: V):
        super().__init__(
            pre_vertex, identifier,
            allowed_edge_types=cast(Type[E], SDRAMMachineEdge))
        self._sdram_size: Optional[int] = None
        self._sdram_base_address: Optional[int] = None

    @overrides(AbstractSingleSourcePartition.add_edge)
    def add_edge(self, edge: E):
        if self._sdram_size is None:
            self._sdram_size = edge.sdram_size
        elif self._sdram_size != edge.sdram_size:
            raise SDRAMEdgeSizeException(
                f"The edges within the constant sdram partition {self} have "
                "inconsistent memory size requests.")
        if self._sdram_base_address is None:
            super().add_edge(edge)
        else:
            raise PacmanConfigurationException(
                "Illegal attempt to add an edge after sdram_base_address set")

    def __missing_edge_msg(self) -> str:
        return f"Partition {self} has no edges"

    @overrides(AbstractSDRAMPartition.total_sdram_requirements)
    def total_sdram_requirements(self) -> int:
        if self._sdram_size is None:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        return self._sdram_size

    @property
    @overrides(AbstractSDRAMPartition.sdram_base_address)
    def sdram_base_address(self) -> int:
        if self._sdram_base_address is None:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value: int):
        if len(self.edges) == 0:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        self._sdram_base_address = new_value
        for edge in self.edges:
            cast(E, edge).sdram_base_address = new_value

    @overrides(AbstractSDRAMPartition.get_sdram_base_address_for)
    def get_sdram_base_address_for(self, vertex: MachineVertex) -> int:
        if self._sdram_base_address is None:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        return self._sdram_base_address

    @overrides(AbstractSDRAMPartition.get_sdram_size_of_region_for)
    def get_sdram_size_of_region_for(self, vertex: MachineVertex) -> int:
        if self._sdram_size is None:
            raise PartitionMissingEdgesException(self.__missing_edge_msg())
        return self._sdram_size
