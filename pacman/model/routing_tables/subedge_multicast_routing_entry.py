from spinn_machine.multicast_routing_entry import MulticastRoutingEntry

class SubedgeMulticastRoutingEntry(MulticastRoutingEntry):
    """ A Multicast Routing Entry that additionally stores the subedges
        associated with the entry
    """

    def __init__(self, key, mask, processor_ids, link_ids, subedges):
        """
        :param key: The routing key
        :type key: int
        :param mask: The route key mask
        :type mask: int
        :param processor_ids: The destination processor ids
        :type processor_ids: iterable of int
        :param link_ids: The destination link ids
        :type link_ids: iterable of int
        :param subedges: The subedges to which this route applies
        :type subedges: iterable of\
                    :py:class:`pacman.model.subgraph.subedge.Subedge`
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def subedges(self):
        """ The subedges to which this routing entry applies

        :return: An iterable of subedges
        :rtype: iterable of :py:class:`pacman.model.subgraph.subedge.Subedge`
        :raise None: does not raise any known exceptions
        """
        pass
    
    def add_subedge(self, subedge, processor_ids, link_ids):
        """ Adds a subedge to the entry adding in the processor_ids and link_ids\
            that are the destination of that subedge.  The pre_subvertex of the\
            subedge must be the same as that for the current subedges.
        
        :param subedge: The subedge to add
        :type subedge: :py:class:`pacman.model.subgraph.subedge.Subedge`
        :param processor_ids: The processor ids that are the destination for\
                    the given subedge
        :type processor_ids: iterable of int
        :param link_ids: The link ids that are the destination for\
                    the given subedge
        :type link_ids: iterable of int
        :return: Nothing is returned
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge does not have the same pre_subvertex as the\
                    existing subedges
        """
        pass
