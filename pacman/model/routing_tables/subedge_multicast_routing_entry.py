class SubedgeMulticastRoutingEntry(object):
    """ Represents a routing entry for a specific subedge of a subgraph.  Note\
        that multiple entries may be merged to create single\
        MulticastRoutingEntry
    """

    def __init__(self, subedge_info, destination_route, source_link_id):
        """

        :param subedge_info: the routing information for a specific subedge
        :type subedge_info:\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :param destination_route: the destination route for the subedge
        :type destination_route:\
                    :py:class:`pacman.model.routing_tables.multicast_route.MulticastRoute`
        :param source_link_id: The id of the link on the source chip from which\
                    the traffic will be received
        :type source_link_id: int
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def subedge_info(self):
        """ The key and mask in the routing entry

        :return: the subedge information
        :rtype: :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
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

    @property
    def source_link_id(self):
        """ The link on the source chip down which the packet was sent

        :return: The link id
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass
