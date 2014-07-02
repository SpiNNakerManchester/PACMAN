class MulticastRoutingEntry(object):
    """ Represents a single routing entry in a router
    """

    def __init__(self, key, mask, destination_route):
        """

        :param key: The key of the route
        :type key: int
        :param mask: The mask of the route
        :type mask: int
        :param destination_route: The destination route
        :type destination_route:\
                    :py:class:`pacman.model.routing_tables.multicast_route.MulticastRoute`
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def key(self):
        """ The key of the routing entry

        :return: The routing key
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass
    
    @property
    def mask(self):
        """ The mask of the routing entry
        
        :return: The mask
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def destination_route(self):
        """ The route to send received packets down

        :return: the route
        :rtype: :py:class:`pacman.model.routing_tables.multicast_route.MulticastRoute`
        :raise None: does not raise any known exceptions
        """
        pass
