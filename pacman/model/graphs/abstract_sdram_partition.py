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

from pacman.model.graphs.abstract_basic_edge_partition import \
    AbstractBasicEdgePartition
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine.machine_sdram_edge import SDRAMMachineEdge
from spinn_utilities.abstract_base import abstractmethod, AbstractBase


@add_metaclass(AbstractBase)
class AbstractSDRAMPartition(AbstractBasicEdgePartition):

    def __init__(self, identifier, label, needs_semaphore=False):
        AbstractBasicEdgePartition.__init__(
            self, identifier=identifier, allowed_edge_types=SDRAMMachineEdge,
            label=label)
        self._traffic_type = EdgeTrafficType.SDRAM
        self._needs_semaphore = needs_semaphore
        self._semaphore_id = None

    @property
    def needs_semaphore(self):
        return self._needs_semaphore

    @property
    def semaphore_id(self):
        return self._semaphore_id

    @semaphore_id.setter
    def semaphore_id(self, new_value):
        self._semaphore_id = new_value

    @abstractmethod
    def total_sdram_requirements(self):
        """ returns the total sdram required by this outgoing partition
        :return: int
        """

    @abstractmethod
    def get_sdram_base_address_for(self, vertex, edge):
        """ return the sdram base address for a edge given which side
        the vertex is on"""

    @abstractmethod
    def get_sdram_size_of_region_for(self, vertex, edge):
        """ returns the size of the region for a vertex given a edge """
