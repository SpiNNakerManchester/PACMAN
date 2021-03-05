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

from pacman.model.routing_tables import AbstractMulticastRoutingTable
from spinn_utilities.overrides import overrides


class CompressedMulticastRoutingTable(AbstractMulticastRoutingTable):
    """ Represents a compressed routing table for a chip.
    """

    __slots__ = [
        # The x-coordinate of the chip for which this is the routing table
        "_x",

        # The y-coordinate of the chip for which this is the routing tables
        "_y",

        # An iterable of routing entries to add to the table
        "_multicast_routing_entries",

        # counter of how many entries in their multicast routing table are
        # defaultable
        "_number_of_defaulted_routing_entries"
    ]

    def __init__(self, x, y, multicast_routing_entries=None):
        """
        :param int x:
            The x-coordinate of the chip for which this is the routing table
        :param int y:
            The y-coordinate of the chip for which this is the routing tables
        :param multicast_routing_entries:
            The routing entries to add to the table
        :type multicast_routing_entries:
            iterable(~spinn_machine.MulticastRoutingEntry)
        :raise pacman.exceptions.PacmanAlreadyExistsException:
            If any two routing entries contain the same key-mask combination
        """
        self._x = x
        self._y = y
        self._number_of_defaulted_routing_entries = 0
        self._multicast_routing_entries = list()

        if multicast_routing_entries is not None:
            for multicast_routing_entry in multicast_routing_entries:
                self.add_multicast_routing_entry(multicast_routing_entry)

    def add_multicast_routing_entry(self, multicast_routing_entry):
        """ Adds a routing entry to this table

        :param multicast_routing_entry: The route to add
        :type multicast_routing_entry:
            ~spinn_machine.MulticastRoutingEntry
        :raise pacman.exceptions.PacmanAlreadyExistsException: If a routing
            entry with the same key-mask combination already exists
        """
        self._multicast_routing_entries.append(multicast_routing_entry)

        # update default routed counter if required
        if multicast_routing_entry.defaultable:
            self._number_of_defaulted_routing_entries += 1

    @property
    @overrides(AbstractMulticastRoutingTable.x)
    def x(self):
        return self._x

    @property
    @overrides(AbstractMulticastRoutingTable.y)
    def y(self):
        return self._y

    @property
    @overrides(AbstractMulticastRoutingTable.multicast_routing_entries)
    def multicast_routing_entries(self):
        return self._multicast_routing_entries

    @property
    @overrides(AbstractMulticastRoutingTable.number_of_entries)
    def number_of_entries(self):
        return len(self._multicast_routing_entries)

    @property
    @overrides(AbstractMulticastRoutingTable.number_of_defaultable_entries)
    def number_of_defaultable_entries(self):
        return self._number_of_defaulted_routing_entries

    @overrides(AbstractMulticastRoutingTable.__eq__)
    def __eq__(self, other):
        if not isinstance(other, CompressedMulticastRoutingTable):
            return False
        if self._x != other.x and self._y != other.y:
            return False
        return self._multicast_routing_entries == \
            other.multicast_routing_entries

    @overrides(AbstractMulticastRoutingTable.__ne__)
    def __ne__(self, other):
        return not self.__eq__(other)

    @overrides(AbstractMulticastRoutingTable.__repr__)
    def __repr__(self):
        entry_string = ""
        for entry in self._multicast_routing_entries:
            entry_string += "{}\n".format(entry)
        return "{}:{}\n\n{}".format(self._x, self._y, entry_string)

    @overrides(AbstractMulticastRoutingTable.__hash__)
    def __hash__(self):
        return id(self)
