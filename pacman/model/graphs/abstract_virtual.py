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

from spinn_utilities.abstract_base import abstractmethod, abstractproperty
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.abstract_vertex import AbstractVertex


@require_subclass(AbstractVertex)
class AbstractVirtual(object):
    """ A vertex which exists outside of the machine, \
        allowing a graph to formally participate in I/O.

    .. note::
        Everything that is an instance of ``AbstractVirtual`` is also an
        instance of :py:class:`AbstractVertex`.
    """

    __slots__ = ()

    @abstractproperty
    def board_address(self):
        """ The IP address of the board to which the device is connected,
            or ``None`` for the boot board, or when using linked chip
            coordinates.

        :rtype: str or None
        """

    @abstractproperty
    def linked_chip_coordinates(self):
        """ The coordinates of the chip to which the device is connected,
            or ``None`` for the boot board, or when using a board address.

        :rtype: tuple(int, int) or None
        """

    @abstractmethod
    def outgoing_keys_and_masks(self):
        """ Get the keys sent by the device or None if there aren't any
            explicitly defined.

        :rtype: list of KeyAndMask or None
        """

    @abstractproperty
    def incoming(self):
        """ Indicates if this device sends traffic into SpiNNaker

        :rtype: bool
        """

    @abstractproperty
    def outgoing(self):
        """ Indicates if this device receives traffic from SpiNNaker

        :rtype: bool
        """

    @abstractmethod
    def get_link_data(self, machine):
        """ Get link data from the machine

        :param Machine machine: The machine to get the data from
        :rtype: AbstractLinkData
        """
