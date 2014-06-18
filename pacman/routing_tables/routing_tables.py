__author__ = 'daviess'


class RoutingTables(object):
    """
    Creates a new object to collect the routing tables and the entries to be\
    used on the SpiNNaker machine
    """

    def __init__(self):
        """

        :return: a RoutingTables object which contains all the routing tables and the routing entries
        :rtype: pacman.routing_tables.routing_tables.RoutingTables
        :raises None: does not raise any known exceptions
        """
        pass

    def add_routing_table(self, routing_table, chip):
        """
        Adds a routing table associated with a particular chip

        :param routing_table: a routing table object to add to the collection
        :param chip: the chip to which this routing table refers
        :type routing_table: pacman.routing_table.routing_table.RoutingTable
        :type chip: pacman.machine.chip.Chip
        :return: None
        :rtype: None
        :raises InvalidChipException: if the specified chip does not exist\
                in the current machine configuration
        """
        pass

    @property
    def routing_tables(self):
        """
        Returns the list of routing table objects

        :return: the list of routing table objects
        :rtype: list of pacman.routing_table.routing_table.RoutingTable
        :raises None: does not raise any known exceptions
        """
        pass
