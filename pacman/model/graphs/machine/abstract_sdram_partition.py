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

from six import add_metaclass

from pacman.model.graphs import AbstractCostedPartition
from pacman.model.graphs.abstract_basic_edge_partition import \
    AbstractBasicEdgePartition
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import SDRAMMachineEdge
from spinn_utilities.abstract_base import abstractmethod, AbstractBase


@add_metaclass(AbstractBase)
class AbstractSDRAMPartition(
        AbstractBasicEdgePartition, AbstractCostedPartition):

    def __init__(self, identifier, label):
        AbstractBasicEdgePartition.__init__(
            self, identifier=identifier, allowed_edge_types=SDRAMMachineEdge,
            label=label)
        AbstractCostedPartition.__init__(self)
        self._traffic_type = EdgeTrafficType.SDRAM
        self._semaphore_id = None

    @abstractmethod
    def total_sdram_requirements(self):
        """ returns the total sdram required by this outgoing partition
        :return: int
        """

    @abstractmethod
    def get_sdram_base_address_for(self, vertex):
        """ return the sdram base address for a edge given which side
        the vertex is on
        :param vertex: the vertex to find sdram base address of
        :return: the sdram address for this vertex
        """

    @abstractmethod
    def get_sdram_size_of_region_for(self, vertex):
        """ returns the size of the region for a vertex given a edge
        :param vertex: the vertex to find sdram size of
        :return: the sdram size for this vertex
        """
