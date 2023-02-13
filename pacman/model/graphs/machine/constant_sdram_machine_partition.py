# Copyright (c) 2019-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from pacman.model.graphs.machine import AbstractSDRAMPartition
from pacman.model.graphs import AbstractSingleSourcePartition
from spinn_utilities.overrides import overrides
from pacman.exceptions import (
    PacmanConfigurationException, PartitionMissingEdgesException,
    SDRAMEdgeSizeException)
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

    def __init__(self, identifier, pre_vertex):
        super().__init__(
            pre_vertex, identifier, allowed_edge_types=SDRAMMachineEdge)
        self._sdram_size = None
        self._sdram_base_address = None

    @overrides(AbstractSingleSourcePartition.add_edge)
    def add_edge(self, edge):
        if self._sdram_size is None:
            self._sdram_size = edge.sdram_size
        elif self._sdram_size != edge.sdram_size:
            raise SDRAMEdgeSizeException(
                "The edges within the constant sdram partition {} have "
                "inconsistent memory size requests.".format(self))
        if self._sdram_base_address is None:
            super().add_edge(edge)
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
        if self._sdram_size is None:
            raise PartitionMissingEdgesException(
                self.MISSING_EDGE_ERROR_MESSAGE.format(self))
        return self._sdram_size
