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
from pacman.model.graphs.machine import AbstractMachineEdgePartition
from spinn_utilities.overrides import overrides
from pacman.exceptions import (
    PacmanConfigurationException, PartitionMissingEdgesException)
from pacman.model.graphs import AbstractMultiplePartition
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import (
    AbstractSDRAMPartition, SDRAMMachineEdge)


class SourceSegmentedSDRAMMachinePartition(
        AbstractMultiplePartition, AbstractSDRAMPartition):

    __slots__ = [
        "_sdram_base_address",
    ]

    def __init__(self, identifier, label, pre_vertices):
        """
        :param str identifier: The identifier of the partition
        :param str label: A label of the partition
        :param iterable(AbstractVertex) pre_vertices:
            The vertices that an edge in this partition may originate at
        """
        super(SourceSegmentedSDRAMMachinePartition, self).__init__(
            pre_vertices, identifier,
            allowed_edge_types=SDRAMMachineEdge, constraints=None,
            label=label, traffic_weight=1,
            class_name="ConstantSdramMachinePartition")
        self._sdram_base_address = None

    @property
    @overrides(AbstractMachineEdgePartition.traffic_type)
    def traffic_type(self):
        return EdgeTrafficType.SDRAM

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
    def add_edge(self, edge, graph_code):
        # check
        if len(self._destinations.keys()) != 1:
            raise PacmanConfigurationException(
                "The MultiSourcePartition can only support 1 destination "
                "vertex")
        if len(self._pre_vertices[edge.pre_vertex]) != 1:
            raise PacmanConfigurationException(
                "The multiple source partition only supports 1 edge from a "
                "given pre vertex.")

        if self._sdram_base_address is not None:
            raise PacmanConfigurationException(
                "Illegal attempt to add an edge after sdram_base_address set")

        # add
        AbstractMachineEdgePartition.check_edge(self, edge)
        AbstractMultiplePartition.add_edge(self, edge, graph_code)

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        self._sdram_base_address = new_value

        for pre_vertex in self._pre_vertices.keys():
            try:
                # allocate for the pre_vertex
                edge = self._pre_vertices[pre_vertex].peek()
                edge.sdram_base_address = new_value
                new_value += edge.sdram_size
            except KeyError:
                raise PartitionMissingEdgesException(
                    "This partition has no edge from {}".format(pre_vertex))

    @overrides(AbstractSDRAMPartition.get_sdram_base_address_for)
    def get_sdram_base_address_for(self, vertex):
        if vertex in self._pre_vertices:
            for edge in self._edges:
                if edge.pre_vertex == vertex:
                    return edge.sdram_base_address
        else:
            return self._sdram_base_address

    @overrides(AbstractSDRAMPartition.get_sdram_size_of_region_for)
    def get_sdram_size_of_region_for(self, vertex):
        if vertex in self._pre_vertices:
            for edge in self._edges:
                if edge.pre_vertex == vertex:
                    return edge.sdram_size
        else:
            return self.total_sdram_requirements()

    @overrides(AbstractMultiplePartition.clone_without_edges)
    def clone_without_edges(self):
        """
        :rtype: SourceSegmentedSDRAMMachinePartition
        """
        return SourceSegmentedSDRAMMachinePartition(
            self._identifier, self._label, self._pre_vertices)
