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

from collections import OrderedDict
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanRoutingException)
from pacman.model.routing_tables import AbstractMulticastRoutingTable
from spinn_utilities.overrides import overrides


class UnCompressedMulticastRoutingTable(AbstractMulticastRoutingTable):
    """ Represents a uncompressed routing table for a chip.
    """

    __slots__ = [
        # The x-coordinate of the chip for which this is the routing table
        "_x",

        # The y-coordinate of the chip for which this is the routing tables
        "_y",

        # An iterable of routing entries to add to the table
        "_multicast_routing_entries",

        # dict of multicast routing entries.
        # (key, mask) -> multicast_routing_entry
        "_entries_by_key_mask",

        # counter of how many entries in their multicast routing table are
        # defaultable
        "_number_of_defaulted_routing_entries",

        #  dict of multicast routing entries. (key) -> entry
        "_entries_by_key"
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
        :raise PacmanAlreadyExistsException:
            If any two routing entries contain the same key-mask combination
        """
        self._x = x
        self._y = y
        self._number_of_defaulted_routing_entries = 0
        self._multicast_routing_entries = list()
        self._entries_by_key_mask = OrderedDict()
        self._entries_by_key = dict()

        if multicast_routing_entries is not None:
            for multicast_routing_entry in multicast_routing_entries:
                self.add_multicast_routing_entry(multicast_routing_entry)

    def add_multicast_routing_entry(self, multicast_routing_entry):
        """ Adds a routing entry to this table

        :param ~spinn_machine.MulticastRoutingEntry multicast_routing_entry:
            The route to add
        :rtype: None
        :raise PacmanAlreadyExistsException:
            If a routing entry with the same key-mask combination already
            exists
        """
        routing_entry_key = multicast_routing_entry.routing_entry_key
        mask = multicast_routing_entry.mask

        tuple_key = (routing_entry_key, mask)
        if tuple_key in self._entries_by_key_mask:
            raise PacmanAlreadyExistsException(
                f"Multicast_routing_entry on {self._x}, {self._y}",
                str(multicast_routing_entry))

        self._entries_by_key_mask[tuple_key] =\
            multicast_routing_entry
        self._entries_by_key[routing_entry_key] = multicast_routing_entry
        self._multicast_routing_entries.append(multicast_routing_entry)

        # update default routed counter if required
        if multicast_routing_entry.defaultable:
            self._number_of_defaulted_routing_entries += 1

    @property
    @overrides(AbstractMulticastRoutingTable.x)
    def x(self):
        """ The x-coordinate of the chip of this table

        :rtype: int
        """
        return self._x

    @property
    @overrides(AbstractMulticastRoutingTable.y)
    def y(self):
        """ The y-coordinate of the chip of this table

        :rtype: int
        """
        return self._y

    @property
    @overrides(AbstractMulticastRoutingTable.multicast_routing_entries)
    def multicast_routing_entries(self):
        """ The multicast routing entries in the table

        :rtype: iterable(~spinn_machine.MulticastRoutingEntry)
        :raise None: does not raise any known exceptions
        """
        return self._multicast_routing_entries

    @property
    @overrides(AbstractMulticastRoutingTable.number_of_entries)
    def number_of_entries(self):
        """ The number of multicast routing entries there are in the\
            multicast routing table

        :rtype: int
        """
        return len(self._multicast_routing_entries)

    @property
    @overrides(AbstractMulticastRoutingTable.number_of_defaultable_entries)
    def number_of_defaultable_entries(self):
        """ The number of multicast routing entries that are set to be\
            defaultable within this multicast routing table

        :rtype: int
        """
        return self._number_of_defaulted_routing_entries

    def get_entry_by_routing_entry_key(self, routing_entry_key):
        """ Get the routing entry associated with the specified key \
            or ``None`` if the routing table does not match the key

        :param int routing_entry_key: the routing key to be searched
        :return: the routing entry associated with the routing key_combo or
            ``None`` if no such entry exists
        :rtype: ~spinn_machine.MulticastRoutingEntry or None
        """
        if routing_entry_key in self._entries_by_key:
            return self._entries_by_key[routing_entry_key]
        return None

    def get_multicast_routing_entry_by_routing_entry_key(
            self, routing_entry_key, mask):
        """ Get the routing entry associated with the specified key_combo-mask\
            combination or ``None`` if the routing table does not match the\
            key_combo

        :param int routing_entry_key: the routing key to be searched
        :param int mask: the routing mask to be searched
        :return: the routing entry associated with the routing key_combo or
            ``None`` if no such entry exists
        :rtype: ~spinn_machine.MulticastRoutingEntry or None
        """
        if (routing_entry_key & mask) != routing_entry_key:
            raise PacmanRoutingException(
                "The key {} is changed when masked with the mask {}."
                " This is determined to be an error in the tool chain. Please "
                "correct this and try again.".format(routing_entry_key, mask))

        tuple_key = (routing_entry_key, mask)
        if tuple_key in self._entries_by_key_mask:
            return self._entries_by_key_mask[
                tuple_key]
        return None

    @overrides(AbstractMulticastRoutingTable.__eq__)
    def __eq__(self, other):
        if not isinstance(other, UnCompressedMulticastRoutingTable):
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
