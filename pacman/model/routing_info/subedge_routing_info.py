class SubedgeRoutingInfo(object):
    """ Associates a subedge to its routing information (key and mask)
    """

    def __init__(self, subedge, key, mask):
        """

        :param subedge: the subedge down which the routing key and mask will be\
                    used
        :type subedge: :py:class:`pacman.model.subgraph.subedge.Subedge`
        :param key: the key which will be sent by the subvertex at the start\
                    of the subedge
        :type key: int
        :param mask: the mask of the key which indicates which bits in the key\
                    are used, and which can be ignored
        :type mask: int
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def subedge(self):
        """ The subedge which the information is about

        :return: the subedge
        :rtype: :py:class:`pacman.model.subgraph.subedge.Subedge`
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def key(self):
        """ The routing key

        :return: the routing key
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def mask(self):
        """ The mask of the routing key

        :return: the mask
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        pass
