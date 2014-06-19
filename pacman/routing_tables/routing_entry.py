__author__ = 'daviess'


class RoutingEntry(object):
    """
    This object represents a single routing entry in a SpiNNaker router,\
    including the routing information, the source and the destination of\
    the projection
    """

    def __init__(self, routing_info, destination_route, source_route):
        """

        :param routing_info: the routing information for a specific subedge
        :param destination_route: the destination route for the specific\
        subedge, expressed as bitmask following the SpiNNaker datasheet
        :param source_route: the source route for the specific subedge,\
        expressed as bitmask following the SpiNNaker datasheet
        :return: a new RoutingEntry object associated with a particular routing table
        :rtype: pacman.routing_tables.routing_entry.RoutingEntry
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def key(self):
        """
        Returns the key in the routing entry

        :return: the key in the routing entry
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def mask(self):
        """
        Returns the mask in the routing entry

        :return: the mask in the routing entry
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def route(self):
        """
        Returns the route in the routing entry expressed as bitmask\
        following the SpiNNaker datasheet

        :return: the route in the routing entry
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def source(self):
        """
        Returns the source route of the incoming projection expressed\
        as bitmask following the SpiNNaker datasheet

        :return: the source route of the incoming projection
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass

