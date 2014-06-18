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
        :rtype: pacman.routing_table.routing_table.RoutingTable
        """
        pass

    def add_routing_entry(self, key, mask, route):
        """

        :param key:
        :param mask:
        :param route:
        :return:
        """
        pass

    @property
    def routing_table(self):
        """

        :return:
        """
        pass
