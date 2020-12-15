# Copyright (c) 2020-2021 The University of Manchester
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
from spinn_utilities.abstract_base import abstractmethod, AbstractBase
from pacman.model.graphs.machine import AbstractMachineEdgePartition


@add_metaclass(AbstractBase)
class AbstractSDRAMPartition(AbstractMachineEdgePartition):

    @abstractmethod
    def total_sdram_requirements(self):
        """ Get the total SDRAM required by this outgoing partition.

        :return: int
        """

    @abstractmethod
    def get_sdram_base_address_for(self, vertex):
        """ Get the SDRAM base address for a edge given which side \
            the vertex is on.

        :param vertex: the vertex to find SDRAM base address of
        :return: the SDRAM address for this vertex
        """

    @abstractmethod
    def get_sdram_size_of_region_for(self, vertex):
        """ Get the size of the region for a vertex given a edge.

        :param vertex: the vertex to find SDRAM size of
        :return: the SDRAM size for this vertex
        """
