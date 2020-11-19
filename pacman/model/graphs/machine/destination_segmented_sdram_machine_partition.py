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
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs import AbstractSingleSourcePartition
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import (
    AbstractSDRAMPartition, SDRAMMachineEdge)


class DestinationSegmentedSDRAMMachinePartition(
        AbstractSingleSourcePartition, AbstractSDRAMPartition):

    __slots__ = [
        "_sdram_base_address",
        "_traffic_type"
    ]

    def __init__(self, identifier, pre_vertex, label):
        super(DestinationSegmentedSDRAMMachinePartition, self).__init__(
            pre_vertex=pre_vertex, identifier=identifier,
            allowed_edge_types=SDRAMMachineEdge, constraints=None,
            label=label, traffic_weight=1,
            class_name="ConstantSdramMachinePartition")
        self._sdram_base_address = None
        self._traffic_type = EdgeTrafficType.SDRAM

    @property
    @overrides(AbstractSDRAMPartition.traffic_type)
    def traffic_type(self):
        return self._traffic_type

    @overrides(AbstractSDRAMPartition.total_sdram_requirements)
    def total_sdram_requirements(self):
        return sum(edge.sdram_size for edge in self.edges)

    @property
    def sdram_base_address(self):
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        self._sdram_base_address = new_value
        for edge in self.edges:
            edge.sdram_base_address = new_value + edge.sdram_size

    @overrides(AbstractSingleSourcePartition.add_edge)
    def add_edge(self, edge, graph_code):
        AbstractSDRAMPartition.check_edge(self, edge)

        # safety check
        if self._pre_vertex != edge.pre_vertex:
            raise PacmanConfigurationException(
                "The destination segmented SDRAM partition only accepts "
                "1 pre-vertex")

        # add
        super(DestinationSegmentedSDRAMMachinePartition, self).add_edge(
            edge, graph_code)

    @overrides(AbstractSDRAMPartition.get_sdram_base_address_for)
    def get_sdram_base_address_for(self, vertex):
        if self._pre_vertex == vertex:
            return self._sdram_base_address
        for edge in self._edges:
            if edge.post_vertex == vertex:
                return edge.sdram_base_address
        return None

    @overrides(AbstractSDRAMPartition.get_sdram_size_of_region_for)
    def get_sdram_size_of_region_for(self, vertex):
        if self._pre_vertex == vertex:
            return self.total_sdram_requirements()
        for edge in self._edges:
            if edge.post_vertex == vertex:
                return edge.sdram_size
        return None

    @overrides(AbstractSingleSourcePartition.clone_for_graph_move)
    def clone_for_graph_move(self):
        """
        :rtype: DestinationSegmentedSDRAMMachinePartition
        """
        return DestinationSegmentedSDRAMMachinePartition(
            self._identifier, self._pre_vertex, self._label)
