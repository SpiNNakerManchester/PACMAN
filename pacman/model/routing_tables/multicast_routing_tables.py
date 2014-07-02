class MulticastRoutingTables(object):
    """ Represents the multicast routing tables for a number of chips
    """

    def __init__(self, routing_tables=None):
        """
        :param routing_tables: The routing tables to add
        :type routing_tables: iterable of\
                    :py:class:`pacman.model.routing_tables.multicast_routing_table.MulticastRoutingTable`
        :raise pacman.exceptions.PacmanAlreadyExistsException: If any two\
                    routing tables are for the same chip
        """
        pass

    def add_routing_table(self, routing_table):
        """ Add a routing table

        :param routing_table: a routing table to add
        :type routing_table:\
                    :py:class:`pacman.model.routing_tables.multicast_routing_table.MulticastRoutingTable`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: If a routing\
                    table already exists for the chip
        """
        pass

    @property
    def routing_tables(self):
        """ The routing tables stored within

        :return: an iterable of routing tables
        :rtype: iterable of\
                    :py:class:`pacman.model.routing_tables.multicast_routing_table.MulticastRoutingTable`
        :raise None: does not raise any known exceptions
        """
        pass
    
    def get_routing_table_for_chip(self, x, y):
        """ Get a routing table for a paricular chip
        
        :param x: The x-coordinate of the chip
        :type x: int
        :param y: The y-coordinate of the chip
        :type y: int
        :return: The routing table, or None if no such table exists
        :rtype:  :py:class:`pacman.model.routing_tables.multicast_routing_table.MulticastRoutingTable`
        :raise None: No known exceptions are raised
        """
        pass
