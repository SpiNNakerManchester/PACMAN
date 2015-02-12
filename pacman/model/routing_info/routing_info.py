from pacman.exceptions import PacmanAlreadyExistsException


class RoutingInfo(object):
    """ An association of a set of subedges to a non-overlapping set of keys\
        and masks
    """

    def __init__(self, subedge_info_items=None):
        """

        :param subedge_info_items: The subedge information items to add
        :type subedge_info_items: iterable of\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
                    or none
        :raise pacman.exceptions.PacmanAlreadyExistsException: If there are\
                    any two items with the same key once the mask is applied\
                    which do not have the same source subvertex
        """
        self._subedge_info_by_key = dict()
        self._subedge_info = list()
        self._key_from_subedge = dict()
        self._subedge_info_from_subedge = dict()
        if subedge_info_items is not None:
            for subedge_info_item in subedge_info_items:
                self.add_subedge_info(subedge_info_item)

    def add_subedge_info(self, subedge_info):
        """ Add a subedge information item

        :param subedge_info: The subedge information item to add
        :type subedge_info:\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: If there is\
                    already an item with the same key once the mask is applied\
                    which does not have the same source subvertex
        """
        if subedge_info.key_mask_combo in self._subedge_info_by_key.keys()\
                and subedge_info.subedge.pre_subvertex is not\
                self._subedge_info_by_key[subedge_info.key_mask_combo]\
                .subedge.pre_subvertex:
            raise PacmanAlreadyExistsException(
                "The key already exists in the routing information",
                str(subedge_info.key_mask_combo))

        self._subedge_info_by_key[subedge_info.key_mask_combo] = subedge_info
        self._subedge_info.append(subedge_info)
        self._key_from_subedge[subedge_info.subedge] = \
            subedge_info.key_mask_combo
        self._subedge_info_from_subedge[subedge_info.subedge] = subedge_info

    @property
    def all_subedge_info(self):
        """ The subedge information for all subedges

        :return: iterable of subedge information
        :rtype: iterable of\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :raise None: does not raise any known exceptions
        """
        return self._subedge_info

    def get_subedge_info_by_key(self, key, mask):
        """ Get the routing information associated with a particular key, once\
            the mask has been applied

        :param key: The routing key
        :type key: int
        :param mask: The routing mask
        :type mask: int
        :return: a routing information associated with the\
                    specified routing key or None if no such key exists
        :rtype:\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :raise None: does not raise any known exceptions
        """
        key_mask_combo = key & mask
        if key_mask_combo in self._subedge_info_by_key.keys():
            return self._subedge_info_by_key[key_mask_combo]
        return None

    def get_key_from_subedge(self, subedge):
        """ Get the key associated with a particular subedge

        :param subedge: The subedge
        :type subedge:
            :py:class:`pacman.model.partitioned_graph.subedge.PartitionedEdge`
        :return: The routing key or None if the subedge does not exist
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        if subedge in self._key_from_subedge.keys():
            return self._key_from_subedge[subedge]
        return None

    def get_subedge_information_from_subedge(self, subedge):
        """ Get the subedge information associated with a particular subedge

        :param subedge: The subedge
        :type subedge:
            :py:class:`pacman.model.partitioned_graph.subedge.PartitionedEdge`
        :return: The subedge information or None if the subedge does not exist
        :rtype:
            :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :raise None: does not raise any known exceptions
        """
        if subedge in self._subedge_info_from_subedge.keys():
            return self._subedge_info_from_subedge[subedge]
        return None
