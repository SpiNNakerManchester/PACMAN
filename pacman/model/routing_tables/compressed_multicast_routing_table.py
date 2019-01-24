from collections import OrderedDict
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanRoutingException)
from pacman.model.routing_tables.abstract_multicast_routing_table import \
    AbsractMulticastRoutingTable
from spinn_utilities.overrides import overrides


class CompressedMulticastRoutingTable(AbsractMulticastRoutingTable):
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
        :param x: \
            The x-coordinate of the chip for which this is the routing table
        :type x: int
        :param y: \
            The y-coordinate of the chip for which this is the routing tables
        :type y: int
        :param multicast_routing_entries: \
            The routing entries to add to the table
        :type multicast_routing_entries: \
            iterable(:py:class:`spinn_machine.MulticastRoutingEntry`)
        :raise pacman.exceptions.PacmanAlreadyExistsException: If any two\
            routing entries contain the same key-mask combination
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
        :type multicast_routing_entry:\
            :py:class:`spinn_machine.MulticastRoutingEntry`
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: If a routing\
            entry with the same key-mask combination already exists
        """
        self._multicast_routing_entries.append(multicast_routing_entry)

        # update default routed counter if required
        if multicast_routing_entry.defaultable:
            self._number_of_defaulted_routing_entries += 1

    @property
    @overrides(AbsractMulticastRoutingTable.x)
    def x(self):
        return self._x

    @property
    @overrides(AbsractMulticastRoutingTable.y)
    def y(self):
        return self._y

    @property
    @overrides(AbsractMulticastRoutingTable.multicast_routing_entries)
    def multicast_routing_entries(self):
        return self._multicast_routing_entries

    @property
    @overrides(AbsractMulticastRoutingTable.number_of_entries)
    def number_of_entries(self):
        return len(self._multicast_routing_entries)

    @property
    @overrides(AbsractMulticastRoutingTable.number_of_defaultable_entries)
    def number_of_defaultable_entries(self):
        return self._number_of_defaulted_routing_entries

    @overrides(AbsractMulticastRoutingTable.__eq__)
    def __eq__(self, other):
        if not isinstance(other, CompressedMulticastRoutingTable):
            return False
        if self._x != other.x and self._y != other.y:
            return False
        return self._multicast_routing_entries == \
            other.multicast_routing_entries

    @overrides(AbsractMulticastRoutingTable.__ne__)
    def __ne__(self, other):
        return not self.__eq__(other)

    @overrides(AbsractMulticastRoutingTable.__repr__)
    def __repr__(self):
        entry_string = ""
        for entry in self._multicast_routing_entries:
            entry_string += "{}\n".format(entry)
        return "{}:{}\n\n{}".format(self._x, self._y, entry_string)

    @overrides(AbsractMulticastRoutingTable.__hash__)
    def __hash__(self):
        return id(self)
