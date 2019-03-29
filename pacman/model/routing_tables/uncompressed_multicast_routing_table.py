try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanRoutingException)
from pacman.model.routing_tables.abstract_multicast_routing_table import \
    AbsractMulticastRoutingTable
from spinn_utilities.overrides import overrides


class UnCompressedMulticastRoutingTable(AbsractMulticastRoutingTable):
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
        self._entries_by_key_mask = OrderedDict()
        self._entries_by_key = dict()

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
        routing_entry_key = multicast_routing_entry.routing_entry_key
        mask = multicast_routing_entry.mask

        tuple_key = (routing_entry_key, mask)
        if tuple_key in self._entries_by_key_mask:
            raise PacmanAlreadyExistsException(
                "Multicast_routing_entry", str(multicast_routing_entry))

        self._entries_by_key_mask[tuple_key] =\
            multicast_routing_entry
        self._entries_by_key[routing_entry_key] = multicast_routing_entry
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

    def get_entry_by_routing_entry_key(self, routing_entry_key):
        """  Get the routing entry associated with the specified key \
            or None if the routing table does not match the key

        :param routing_entry_key: the routing key to be searched
        :type routing_entry_key: int
        :return the routing entry associated with the routing key_combo or\
            None if no such entry exists
        :rtype:\
            :py:class:`spinn_machine.MulticastRoutingEntry`
        """
        if routing_entry_key in self._entries_by_key:
            return self._entries_by_key[routing_entry_key]
        return None

    def get_multicast_routing_entry_by_routing_entry_key(
            self, routing_entry_key, mask):
        """ Get the routing entry associated with the specified key_combo-mask\
            combination or None if the routing table does not match the\
            key_combo

        :param routing_entry_key: the routing key to be searched
        :type routing_entry_key: int
        :param mask: the routing mask to be searched
        :type mask: int
        :return: the routing entry associated with the routing key_combo or\
            None if no such entry exists
        :rtype:\
            :py:class:`spinn_machine.MulticastRoutingEntry`
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

    @overrides(AbsractMulticastRoutingTable.__eq__)
    def __eq__(self, other):
        if not isinstance(other, UnCompressedMulticastRoutingTable):
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
