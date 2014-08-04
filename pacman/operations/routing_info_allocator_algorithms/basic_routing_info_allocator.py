from pacman.model.constraints.abstract_router_constraint import \
    AbstractRouterConstraint
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.operations.routing_info_allocator_algorithms.\
    abstract_routing_info_allocator_algorithm import \
    AbstractRoutingInfoAllocatorAlgorithm
from pacman.utilities import utility_calls
from pacman.utilities import constants


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
        self._used_masks = dict()

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
        #check that this algorithum supports the constraints put onto the
        #subvertexes
        utility_calls.check_algorithum_can_support_constraints(
            object_list=subgraph.subvertices,
            supported_constraints=self._supported_constrants,
            constraint_check_level=AbstractRouterConstraint)

        #take each subedge and create keys from its placement
        routing_infos = RoutingInfo()
        for subvert in subgraph.subvertices:
            out_going_subedges = \
                subgraph.outgoing_subedges_from_subvertex(subvert)
            for out_going_subedge in out_going_subedges:
                placement = placements.get_placement_of_subvertex(subvert)
                routing_infos.add_subedge_info(
                    self._allocate_subedge_key_mask(out_going_subedge,
                                                    placement))
        return routing_infos

    def _allocate_subedge_key_mask(self, out_going_subedge, placement):
        """helper method (can be overlaoded by future impliemntations of key
        alloc

        :param out_going_subedge: the outgoing subedge from a given subvert
        :param placement: the placement for the given subvert
        :type out_going_subedge: pacman.model.subgraph.subegde.Subedge
        :type placement: pacman.model.placements.placement.Placement
        :return: a subedge_routing_info which contains the key, and mask of the\
         subvert
         :rtype:
        """
        key = self._get_key_from_placement(placement)
        subedge_routing_info = SubedgeRoutingInfo(
            key=key, mask=constants.DEFAULT_MASK, subedge=out_going_subedge)
        #check for storage of masks
        self.check_masks(constants.DEFAULT_MASK, key)
        return subedge_routing_info

    @staticmethod
    def _get_key_from_placement(placement):
        """

        """
        return placement.x << 24 | placement.y << 16 | placement.p << 11

    def check_masks(self, new_mask, key):
        """

        """
        if new_mask not in self._used_masks:
            self._used_masks[new_mask] = list()
        #add to list (newly created or otherwise)
        self._used_masks[new_mask].append(key)

    @staticmethod
    def get_key_mask_combo(key, mask):
        """

        """
        combo = key & mask
        return combo