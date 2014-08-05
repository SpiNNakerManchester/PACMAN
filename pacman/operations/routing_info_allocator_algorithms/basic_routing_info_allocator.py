from pacman.model.constraints.abstract_router_constraint import \
    AbstractRouterConstraint
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.operations.routing_info_allocator_algorithms.\
    abstract_routing_info_allocator_algorithm import \
    AbstractRoutingInfoAllocatorAlgorithm
from pacman.utilities import utility_calls
from pacman.utilities import constants
from pacman import exceptions


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
        AbstractRoutingInfoAllocatorAlgorithm.__init__(
            self, graph_to_sub_graph_mapper)

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
        #check that this algorithm supports the constraints put onto the
        #subvertexes
        utility_calls.check_algorithm_can_support_constraints(
            object_list=subgraph.subvertices,
            supported_constraints=self._supported_constraints,
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
         :rtype: pacman.model.routing_info.subegde_rotuing_info.SubedgeRoutingInfo
         :raise None: does not raise any known exceptions
        """
        key = self._get_key_from_placement(placement)
        subedge_routing_info = SubedgeRoutingInfo(
            key=key, mask=constants.DEFAULT_MASK, subedge=out_going_subedge)
        #check for storage of masks
        self.check_masks(constants.DEFAULT_MASK, key, placement.subvertex)
        return subedge_routing_info

    @staticmethod
    def _get_key_from_placement(placement):
        """returns a key given a placement
        :param placement: the associated placement
        :type placement: pacman.model.placements.placement.Placement
        :return a int reperenstation of the key
        :rtype: int
        :raise None: does not raise any known expcetions
        """
        return placement.x << 24 | placement.y << 16 | placement.p << 11

    def check_masks(self, mask, key, subvert):
        """checks that the mask and key together havent been used before by\
        another subvertex

        :param mask: the mask used by the subvertex
        :param key: the key used by the subvert
        :param subvert: the subvert the key and mask are used by
        :type mask: int
        :type key: int
        :type subvert: pacman.model.subgraph.subvertex.Subvertex
        :return: None
        :rtype: None
        :raise PacmanRouteInfoAllocationException: when 2 or more subvertices \
        are using the same key and mask
        """
        if mask not in self._used_masks:
            self._used_masks[mask] = list()
        #add to list (newly created or otherwise)
        if key in self._used_masks[mask] \
                and self._subvert_to_key_mapper[key] != subvert:
            raise exceptions.PacmanRouteInfoAllocationException(
                "this key and mask have been used by another subvertex already"
                "and therefore cannot be used again. Please fix and try again")
        self._used_masks[mask].append(key)
        self._subvert_to_key_mapper[self.get_key_mask_combo(key, mask)] = \
            subvert

    @staticmethod
    def get_key_mask_combo(key, mask):
        """return the key mask combo

        :param key: the key used by this subedge
        :param mask: the mask used by this subedge
        :type key: int
        :type mask: int
        :return: the key mask combo in int form
        :rtype: int
        :raise None: this method does not raise any known exceptions
        """
        combo = key & mask
        return combo