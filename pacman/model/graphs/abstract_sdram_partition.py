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

    def __init__(self, identifier, label):
        AbstractBasicEdgePartition.__init__(
            self, identifier=identifier, allowed_edge_types=SDRAMMachineEdge,
            label=label)
        self._traffic_type = EdgeTrafficType.SDRAM

    @abstractmethod
    def total_sdram_requirements(self):
        """ returns the total sdram required by this outgoing partition
        :return: int
        """
