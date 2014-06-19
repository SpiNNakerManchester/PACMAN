__author__ = 'daviess'


class Info(object):
    """
    Associates a subedge to its routing information (key and mask)
    """

    def __init__(self, subedge, key, mask):
        """

        :param subedge: the subedge to associate with the\
               routing key and the mask
        :param keys: the routing key of a specific subedge
        :param mask: the mask of a specific subedge
        :type subedge: pacman.subgraph.subvertex.Subvertex
        :type keys: int
        :type mask: int
        :return: the new routing_info association
        :rtype: pacman.routing_info.routing_info.RoutingInfo
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def subedge(self):
        """
        Returns the subedge object

        :return: the subedge object
        :rtype: pacman.subgraph.subedge.Subedge
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def key(self):
        """
        Returns the routing key

        :return: the routing key
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def mask(self):
        """
        Returns the mask of the routing key

        :return: the mask
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass
