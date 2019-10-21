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

from pacman.model.graphs.abstract_multiple_partition import \
    AbstractMultiplePartition
from pacman.model.graphs.abstract_sdram_partition import AbstractSDRAMPartition
from spinn_utilities.overrides import overrides


class BothSegmentedSDRAMMachinePartition(
        AbstractMultiplePartition, AbstractSDRAMPartition):

    __slots__ = [
        "_sdram_base_address",
        "_pre_vertex_map"
    ]

    def __init__(self, identifier, label, pre_vertices):
        AbstractMultiplePartition.__init__(self, pre_vertices)
        AbstractSDRAMPartition.__init__(self, identifier, label)
        self._sdram_base_address = None
        self._pre_vertex_map = dict()

    def total_sdram_requirements(self):
        total = 0
        for edge in self.edges:
            total += edge.sdram_size
        return total

    @overrides(AbstractSDRAMPartition.add_edge)
    def add_edge(self, edge):
        # add
        AbstractMultiplePartition.add_edge(self, edge)
        AbstractSDRAMPartition.add_edge(self, edge)

    @property
    def sdram_base_address(self):
        return self._sdram_base_address

    def destination_sdram_base_address(self, edge):
        return self._pre_vertex_map[edge]

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        self._sdram_base_address = new_value

        for destination in self._destinations.keys():

            # allocate for the pre_vertex
            base_address = new_value
            for edge in self._destinations[destination]:

                # set to next sdram address
                edge.sdram_base_address = new_value

                # this edge is part of a destination, so gets the same base
                # address in the map
                self._pre_vertex_map[edge] = base_address

                # update new sdram location
                new_value += edge.sdram_size
