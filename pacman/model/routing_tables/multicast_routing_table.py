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
        pass

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
        pass
    
    @property
    def x(self):
        """ The x-coordinate of the chip of this table
        
        :return: The x-coordinate
        :rtype: int
        """
        pass
    
    @property
    def y(self):
        """ The y-coordinate of the chip of this table
        
        :return: The y-coordinate
        :rtype: int
        """
        pass

    @property
    def multicast_routing_entries(self):
        """ The multicast routing entries in the table

        :return: an iterable of multicast routing entries
        :rtype: iterable of\
                    :py:class:`spinn_machine.multicast_routing_entry.MulticastRoutingEntry`
        :raise None: does not raise any known exceptions
        """
        pass
    
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
        pass
