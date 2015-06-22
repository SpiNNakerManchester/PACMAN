from collections import OrderedDict
from pacman import exceptions


class MulticastRoutingTable(object):
    """ Represents a routing table for a chip
    """

    def __init__(self, x, y, multicast_routing_entries=None):
        """

        :param x: The x-coordinate of the chip for which this is the routing\
                    table
        :type x: int
        :param y: The y-coordinate of the chip for which this is the routing\
                    tables
        :type y: int
        :param multicast_routing_entries: An iterable of routing entries to\
                    add to the table
        :type multicast_routing_entries: iterable of\
                    :py:class:`spinn_machine.multicast_routing_entry.MulticastRoutingEntry`
        :raise pacman.exceptions.PacmanAlreadyExistsException: If any two\
                    routing entries contain the same key-mask combination
        """
        self._x = x
        self._y = y
        self._multicast_routing_entries = set()
        self._multicast_routing_entries_by_routing_entry_key = OrderedDict()

        if multicast_routing_entries is not None:
            for multicast_routing_entry in multicast_routing_entries:
                self.add_mutlicast_routing_entry(multicast_routing_entry)

    def add_mutlicast_routing_entry(self, multicast_routing_entry):
        """ Adds a routing entry to this table

        :param multicast_routing_entry: The route to add
        :type multicast_routing_entry:\
                    :py:class:`spinn_machine.multicast_routing_entry.MulticastRoutingEntry`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: If a routing\
                    entry with the same key-mask combination already exists
        """
        routing_entry_key = multicast_routing_entry.routing_entry_key
        mask = multicast_routing_entry.mask

        tuple_key = (routing_entry_key, mask)
        if tuple_key in self._multicast_routing_entries_by_routing_entry_key:
            raise exceptions.PacmanAlreadyExistsException(
                "Multicast_routing_entry", str(multicast_routing_entry))

        self._multicast_routing_entries_by_routing_entry_key[tuple_key] =\
            multicast_routing_entry
        self._multicast_routing_entries.add(multicast_routing_entry)

    def remove_multicast_routing_entry(self, multicast_routing_entry):
        """removes a multicast entry from this table

        :param multicast_routing_entry: The route to remove
        :type multicast_routing_entry:\
                    :py:class:`spinn_machine.multicast_routing_entry.MulticastRoutingEntry`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanNotExistException: If a routing\
                    entry with the same key-mask combination already exists
        """
        routing_entry_key = multicast_routing_entry.routing_entry_key
        mask = multicast_routing_entry.mask

        tuple_key = (routing_entry_key, mask)
        if tuple_key in self._multicast_routing_entries_by_routing_entry_key:
            del self._multicast_routing_entries_by_routing_entry_key[tuple_key]
            self._multicast_routing_entries.remove(multicast_routing_entry)
        else:
            raise exceptions.PacmanNotExistException(
                "Multicast_routing_entry {} does not exist, and therefore "
                "cannot be removed from routing table {}"
                .format(multicast_routing_entry, self))

    @property
    def x(self):
        """ The x-coordinate of the chip of this table

        :return: The x-coordinate
        :rtype: int
        """
        return self._x

    @property
    def y(self):
        """ The y-coordinate of the chip of this table

        :return: The y-coordinate
        :rtype: int
        """
        return self._y

    @property
    def multicast_routing_entries(self):
        """ The multicast routing entries in the table

        :return: an iterable of multicast routing entries
        :rtype: iterable of\
                    :py:class:`spinn_machine.multicast_routing_entry.MulticastRoutingEntry`
        :raise None: does not raise any known exceptions
        """
        return self._multicast_routing_entries

    @property
    def number_of_entries(self):
        """
        returns the number of multi-cast routing entries there are in the
        multicast routing table
        :return:
        """
        return len(self._multicast_routing_entries)

    def get_multicast_routing_entry_by_routing_entry_key(
            self, routing_entry_key, mask):
        """ Get the routing entry associated with the specified key_combo-mask\
            combination or None if the routing table does not match the\
            key_combo

        :param routing_entry_key: the routing key_combo to be searched
        key_combope key: int
        :param mask: the routing mask to be searched
        :type mask: int
        :return: the routing entry associated with the routing key_combo or\
                    None if no such entry exists
        :rtype:\
                    :py:class:`spinn_machine.multicast_routing_entry.MulticastRoutingEntry`
        :raise None: does not raise any known exceptions
        """
        if (routing_entry_key & mask) != routing_entry_key:
            raise exceptions.PacmanRoutingException(
                "The key combo {} is changed when masked with the mask {}. This"
                " is determined to be an error in the tool chain. Please "
                "correct this and try again.".format(routing_entry_key, mask))

        tuple_key = (routing_entry_key, mask)
        if tuple_key in self._multicast_routing_entries_by_routing_entry_key:
            return self._multicast_routing_entries_by_routing_entry_key[
                tuple_key]
        return None
