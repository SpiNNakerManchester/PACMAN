import collections

__subedge_routing_info = collections.namedtuple(
    'SubedgeRoutingInfo', 'subedge key mask key_mask_combo')


def SubedgeRoutingInfo(subedge, key, mask):
        """Create a new representation of the routing information for a subedge

        :param subedge: the subedge down which the routing key and mask will be
                        used
        :type subedge: :py:class:`pacman.model.subgraph.subedge.PartitionedEdge`
        :param int key: the key which will be sent by the subvertex at the
                        start of the subedge
        :param int mask: the mask of the key which indicates which bits in the
                         key are used, and which can be ignored
        :raise None: does not raise any known exceptions
        """
        kmc = key & mask
        return __subedge_routing_info(subedge, key, mask, kmc)
