__author__ = 'daviess'


class RoutingInfo(object):
    """
    Creates a routing info object which associates keys and masks to subedges
    """

    def __init__(self):
        """

        :return: a new RoutingInfo object
        :rtype: pacman.routing_info.routing_info.RoutingInfo
        :raise None: does not raise any known exceptions
        """
        pass

    def add_routing_info(self, subedge, keys, mask):
        """
        Associate a set of key and mask to a subedge

        :param subedge: the subedge to associate with the\
               routing key and the mask
        :param keys: the routing key of a specific subedge
        :param mask: the mask of a specific subedge
        :type subedge: pacman.subgraph.subvertex.Subvertex
        :type keys: int
        :type mask: int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def routing_info(self):
        """
        Returns the list of routing info association

        :return: list of routing information
        :rtype: list of pacman.routing_info.info.Info
        :raise None: does not raise any known exceptions
        """
        pass

    def find_routing_info_from_key(self, key):
        """
        Finds the routing information associated with a particular key

        :param key: the key to look for in the collection of routing information
        :type key: int

        :return: the routing information associated with the specified routing key or None
        :rtype: pacman.routing_info.info.Info or None
        :raise None: does not raise any known exceptions
        """
        pass

    def find_routing_info_from_subedge(self, subedge):
        """
        Finds the routing information associated with a particular subedge

        :param subedge: the key to look for in the collection of routing information
        :type subedge: pacman.subgraph.subvertex.Subvertex

        :return: the routing information associated with the specified subvertex or None
        :rtype: pacman.routing_info.info.Info or None
        :raise None: does not raise any known exceptions
        """
        pass
