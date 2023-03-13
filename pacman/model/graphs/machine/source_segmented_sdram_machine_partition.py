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
from spinn_utilities.overrides import overrides
from pacman.exceptions import (
    PacmanConfigurationException, PartitionMissingEdgesException)
from pacman.model.graphs import AbstractMultiplePartition
from pacman.model.graphs.machine import (
    AbstractSDRAMPartition, SDRAMMachineEdge)


class SourceSegmentedSDRAMMachinePartition(
        AbstractMultiplePartition, AbstractSDRAMPartition):
    """
    An SDRAM partition that gives each edge its own slice of memory from a
    contiguous block. The edges all have the same destination vertex.
    """
    __slots__ = [
        "_sdram_base_address",
    ]

    def __init__(self, identifier, pre_vertices):
        """
        :param str identifier: The identifier of the partition
        :param str label: A label of the partition
        :param iterable(AbstractVertex) pre_vertices:
            The vertices that an edge in this partition may originate at
        """
        super().__init__(
            pre_vertices, identifier, allowed_edge_types=SDRAMMachineEdge)
        self._sdram_base_address = None

    def total_sdram_requirements(self):
        """
        :rtype: int
        """
        return sum(edge.sdram_size for edge in self.edges)

    @property
    def sdram_base_address(self):
        """
        :rtype: int
        """
        return self._sdram_base_address

    @overrides(AbstractMultiplePartition.add_edge)
    def add_edge(self, edge):
        # check
        if len(self._destinations):
            if edge.post_vertex not in self._destinations:
                raise PacmanConfigurationException(
                    "The {} can only support 1 destination vertex".format(
                        self.__class__.__name__))
        try:
            if len(self._pre_vertices[edge.pre_vertex]) != 0:
                raise PacmanConfigurationException(
                    f"The {self.__class__.__name__} only supports 1 edge from "
                    f"a given pre vertex.")
        except KeyError as ex:
            raise PacmanConfigurationException(
                "Edge pre_vertex is not a Partition. pre vertex") from ex
        # add
        super().add_edge(edge)

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        if len(self.pre_vertices) != len(self.edges):
            raise PartitionMissingEdgesException(
                f"There are {len(self.pre_vertices)} pre vertices "
                f"but only {len(self.edges)} edges")

        self._sdram_base_address = new_value

        for pre_vertex in self._pre_vertices.keys():
            # allocate for the pre_vertex
            edge = self._pre_vertices[pre_vertex].peek()
            edge.sdram_base_address = new_value
            new_value += edge.sdram_size

    @overrides(AbstractSDRAMPartition.get_sdram_base_address_for)
    def get_sdram_base_address_for(self, vertex):
        if self._sdram_base_address is None:
            return None
        if vertex in self._pre_vertices:
            edge = self._pre_vertices[vertex].peek()
            return edge.sdram_base_address
        else:
            return self._sdram_base_address

    @overrides(AbstractSDRAMPartition.get_sdram_size_of_region_for)
    def get_sdram_size_of_region_for(self, vertex):
        if vertex in self._pre_vertices:
            edge = self._pre_vertices[vertex].peek()
            return edge.sdram_size
        else:
            return self.total_sdram_requirements()
