from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.operations.routing_info_allocator_algorithms.\
    abstract_routing_info_allocator_algorithm import \
    AbstractRoutingInfoAllocatorAlgorithm


class BasicRoutingInfoAllocator(AbstractRoutingInfoAllocatorAlgorithm):
    """ An basic algorithm that can produce routing keys and masks for\
        subedges in a subgraph based on the x,y,p of their placement
    """

    def __init__(self, graph_to_sub_graph_mapper):
        """constructor that build a
        pacman.operations.routing_info_allocator_algorithms.BasicRoutingInfoAllocator

        :param graph_to_sub_graph_mapper: the mappings betweeen graph and \
        subgraph
        :type graph_to_sub_graph_mapper: pacman.model.graoh_subgraph_mapper.graph_subgraph_mapper.GraphSubgraphMapper
        :return: a new basic routing key info allocator
        :rtype: pacman.operations.routing_info_allocator_algorithms.basic_routing_info_allocator.BasicRoutingInfoAllocator
        :raise None: this method does not raise any known exception

        """
        AbstractRoutingInfoAllocatorAlgorithm.__init__(self)
        self._graph_to_sub_graph_mapper = graph_to_sub_graph_mapper

    def allocate_routing_info(self, subgraph, placements):
        """ Allocates routing information to the subedges in a subgraph

        :param subgraph: The subgraph to allocate the routing info for
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param placements: The placements of the subvertices
        :type placements: :py:class:`pacman.model.placements.placements.Placements`
        :return: The routing information
        :rtype: :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: If\
                   something goes wrong with the allocation
        """
        routing_infos = RoutingInfo()
        for subvert in subgraph.subvertices:
            out_going_subedges = \
                subgraph.outgoing_subedges_from_subvertex(subvert)
            for out_going_subedge in out_going_subedges:
                routing_infos.add_subedge_info(
                    self._allocate_subedge_key_mask(out_going_subedge))
        return routing_infos

    def _allocate_subedge_key_mask(self, out_going_subedge):





