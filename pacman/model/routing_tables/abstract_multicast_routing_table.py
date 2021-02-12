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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractproperty, abstractmethod)


class AbstractMulticastRoutingTable(object, metaclass=AbstractBase):
    """ A multicast routing table. Might be compressed or uncompressed.
    """

    @abstractproperty
    def x(self):
        """ The x-coordinate of the chip of this table

        :rtype: int
        """

    @abstractproperty
    def y(self):
        """ The y-coordinate of the chip of this table

        :rtype: int
        """

    @abstractproperty
    def multicast_routing_entries(self):
        """ The multicast routing entries in the table

        :rtype: iterable(~spinn_machine.MulticastRoutingEntry)
        """

    @abstractproperty
    def number_of_entries(self):
        """ The number of multi-cast routing entries there are in the\
            multicast routing table

        :rtype: int
        """

    @abstractproperty
    def number_of_defaultable_entries(self):
        """ The number of multi-cast routing entries that are set to be\
            defaultable within this multicast routing table

        :rtype: int
        """

    @abstractmethod
    def __eq__(self, other):
        """equals method"""

    @abstractmethod
    def __ne__(self, other):
        """ not equals method"""

    @abstractmethod
    def __hash__(self):
        """hash"""

    @abstractmethod
    def __repr__(self):
        """repr"""
