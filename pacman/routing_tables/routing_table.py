__author__ = 'daviess'


class RoutingTable(object):
    """
    Creates a new object to collect the routing entries of a SpiNNaker chip\
    at a given location
    """

    def __init__(self, chip):
        """

        :param chip: the chip to which the routing table refers
        :type chip: pacman.machine.chip.Chip
        :return: a new RoutingTable object associated with a particular chip
        :rtype: pacman.routing_tables.routing_table.RoutingTable
        :raise None: does not raise any known exceptions
        """
        pass

    def add_routing_entry(self, routing_info, route_destination, route_source):
        """
        Adds a routing entry for a specific chip

        :param routing_info: the routing information related to the specific subedge (key and mask)
        :param route_destination: the destination of the route on the\
        particular chip. This value follows the definition of the "route"\
        field of the router in the SpiNNaker datasheet
        :param route_source: the incoming direction of the route on the\
        particular chip. This value follows the definition of the "route"\
        field of the router in the SpiNNaker datasheet
        :type routing_info: pacman.routing_info.routing_info.RoutingInfo
        :type route_destination: int
        :type route_source: int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def routing_table(self):
        """
        Returns the list of routing entries in the routing table or None if\
        the routing table is empty

        :return: the list of routing entries in the routing table
        :rtype: list of pacman.routing_tables.routing_entry.RoutingEntry or None
        :raise None: does not raise any known exceptions
        """
        pass

    def get_routing_entry_form_key(self, key):
        """
        Returns the routing entry(-ies) associated with the specified key or\
        None if the routing table does not contain any

        :param key: the routing key to be searched
        :type key: int
        :return: the list of routing entries associated with the routing key
        :rtype: list of pacman.routing_tables.routing_entry.RoutingEntry or None
        :raise None: does not raise any known exceptions
        """
        pass

    def get_routing_entry_form_routing_info(self, routing_info):
        """
        Returns the routing entry(-ies) associated with the specified\
        routing_info or None if the routing table does not contain any

        :param routing_info: the routing info to be searched
        :type routing_info: pacman.routing_info.routing_info.RoutingInfo
        :return: the list of routing entries associated with the routing info
        :rtype: list of pacman.routing_tables.routing_entry.RoutingEntry or None
        :raise None: does not raise any known exceptions
        """
        pass