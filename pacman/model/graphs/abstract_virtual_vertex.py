# Copyright (c) 2017-2019 The University of Manchester
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

from spinn_utilities.abstract_base import (
    abstractmethod, abstractproperty)
from .abstract_vertex import AbstractVertex


class AbstractVirtualVertex(AbstractVertex):
    """ A vertex which exists outside of the machine, allowing a graph to\
        formally participate in I/O.
    """

    __slots__ = ()

    @abstractproperty
    def board_address(self):
        """ The IP address of the board to which the device is connected,\
            or None for the boot board.

        :rtype: str
        """

    @abstractmethod
    def set_virtual_chip_coordinates(self, virtual_chip_x, virtual_chip_y):
        """ Set the details of the virtual chip that has been added to the\
            machine for this vertex.

        :param virtual_chip_x: The x-coordinate of the added chip
        :param virtual_chip_y: The y-coordinate of the added chip
        """

    @abstractproperty
    def virtual_chip_x(self):
        """ The x-coordinate of the virtual chip where this vertex is to be\
            placed.

        :rtype: int
        """

    @abstractproperty
    def virtual_chip_y(self):
        """ The y-coordinate of the virtual chip where this vertex is to be\
            placed.

        :rtype: int
        """
