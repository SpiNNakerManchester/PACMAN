from pacman.exceptions import PacmanAlreadyExistsException


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
        :param multicast_routing_entries: An iterable of routing entries to add\
                    to the table
        :type multicast_routing_entries: iterable of\
                    :py:class:`spinn_machine.multicast_routing_entry.MulticastRoutingEntry`
        :raise pacman.exceptions.PacmanAlreadyExistsException: If any two\
                    routing entries contain the same key-mask combination
        """
        self._x = x
        self._y = y
        self._multicast_routing_entries = set()
        self._multicast_routing_entries_by_key = dict()

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
        key_mask_combo = multicast_routing_entry.key & multicast_routing_entry.mask
        if key_mask_combo not in\
                self._multicast_routing_entries_by_key.keys():
            self._multicast_routing_entries_by_key[key_mask_combo] = set()

        if key_mask_combo in\
                self._multicast_routing_entries_by_key[key_mask_combo]:
            raise PacmanAlreadyExistsException("Multicast_routing_entry", str(multicast_routing_entry))

        self._multicast_routing_entries_by_key[key_mask_combo].add(multicast_routing_entry)
        self._multicast_routing_entries.add(multicast_routing_entry)
    
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
    
    def get_multicast_routing_entry_by_key(self, key, mask):
        """ Get the routing entry associated with the specified key-mask\
            combination or None if the routing table does not match the key

        :param key: the routing key to be searched
        :type key: int
        :param mask: the routing mask to be searched
        :type mask: int
        :return: the routing entry associated with the routing key or None if\
                    no such entry exists
        :rtype: :py:class:`spinn_machine.multicast_routing_entry.MulticastRoutingEntry`
        :raise None: does not raise any known exceptions
        """
        if key & mask in self._multicast_routing_entries_by_key.keys():
            return self._multicast_routing_entries_by_key[key & mask]
        return None
