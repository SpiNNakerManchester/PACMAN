# pacman imports
from pacman import exceptions


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
        :raise pacman.exceptions.PacmanAlreadyExistsException: If there are \
                    two subedge information objects with the same edge
        """

        # List of subedge information indexed by routing key (int)
        self._subedge_infos_by_key = dict()

        # Subedge information indexed by subedge
        self._subedge_info_by_subedge = dict()

        # key_masks_ indexed by subvertex
        self._key_masks_by_subvertex = dict()

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
        :raise pacman.exceptions.PacmanAlreadyExistsException: If the subedge\
                    is already in the set of subedges
        """

        if subedge_info.subedge in self._subedge_info_by_subedge:
            raise exceptions.PacmanAlreadyExistsException(
                "PartitionedEdge", str(subedge_info.subedge))

        self._subedge_info_by_subedge[subedge_info.subedge] = subedge_info

        for key_and_mask in subedge_info.keys_and_masks:

            # first time the key has been added
            if key_and_mask.key not in self._subedge_infos_by_key:
                self._subedge_infos_by_key[key_and_mask.key] = list()
                self._subedge_infos_by_key[key_and_mask.key]\
                    .append(subedge_info)

            # need to check that subedge infos are linked properly
            elif self._subedge_infos_by_key[key_and_mask.key] != subedge_info:
                self._subedge_infos_by_key[key_and_mask.key]\
                    .append(subedge_info)

        # add the key mask by subvertex mapping
        pre_sub = subedge_info.subedge.pre_subvertex
        if pre_sub not in self._key_masks_by_subvertex:
            self._key_masks_by_subvertex[pre_sub] = list()
        for key_and_mask in subedge_info.keys_and_masks:
            self._key_masks_by_subvertex[pre_sub].append(key_and_mask)

    @property
    def all_subedge_info(self):
        """ The subedge information for all subedges

        :return: iterable of subedge information
        :rtype: iterable of\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :raise None: does not raise any known exceptions
        """
        return self._subedge_info_by_subedge.itervalues()

    def get_key_and_masks_for_partitioned_vertex(self, partitioned_vertex):
        """ Get the keys and masks which this partitioned vertex uses when
            transmitting packets

        :param partitioned_vertex: the partitioned vertex to locate its\
                    key_masks for
        :type partitioned_vertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :return: an iterable of keys and masks for the partitioned vertex
        :rtype: iterable of \
                    :py:class:`pacman.model.routing_info.key_and_mask.BaseKeyAndMask`
        """
        if partitioned_vertex in self._key_masks_by_subvertex:
            return self._key_masks_by_subvertex[partitioned_vertex]
        else:
            return list()

    def get_subedge_infos_by_key(self, key, mask):
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
        if key_mask_combo in self._subedge_infos_by_key:
            return self._subedge_infos_by_key[key_mask_combo]
        return None

    def get_keys_and_masks_from_subedge(self, subedge):
        """ Get the key associated with a particular subedge

        :param subedge: The subedge
        :type subedge:
                    :py:class:`pacman.model.partitioned_graph.multi_cast_partitioned_edge.MultiCastPartitionedEdge`
        :return: The routing key or None if the subedge does not exist
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        if subedge in self._subedge_info_by_subedge:
            return self._subedge_info_by_subedge[subedge].keys_and_masks
        return None

    def get_subedge_information_from_subedge(self, subedge):
        """ Get the subedge information associated with a particular subedge

        :param subedge: The subedge
        :type subedge:
                    :py:class:`pacman.model.partitioned_graph.multi_cast_partitioned_edge.MultiCastPartitionedEdge`
        :return: The subedge information or None if the subedge does not exist
        :rtype:
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :raise None: does not raise any known exceptions
        """
        if subedge in self._subedge_info_by_subedge:
            return self._subedge_info_by_subedge[subedge]
        return None

    def __iter__(self):
        """ returns a iterator for the subedge routing infos

        :return: a iterator of subedge routing infos
        """
        return iter(self._subedge_infos_by_key)
