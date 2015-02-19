from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.operations.routing_info_allocator_algorithms.\
    abstract_routing_info_allocator_algorithm import \
    AbstractRoutingInfoAllocatorAlgorithm
from pacman.utilities import utility_calls
from pacman.utilities.progress_bar import ProgressBar
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.model.routing_info.key_and_mask import KeyAndMask
from pacman.model.constraints.abstract_key_allocator_constraint \
    import AbstractKeyAllocatorConstraint

MAX_KEYS_SUPPORTED = 2048
MASK = 0xFFFFF800


class BasicRoutingInfoAllocator(AbstractRoutingInfoAllocatorAlgorithm):
    """ An basic algorithm that can produce routing keys and masks for\
        edges in a partitioned_graph based on the x,y,p of the placement\
        of the preceding partitioned vertex.
        Note that no constraints are supported, and that the number of keys\
        required by each edge must be 2048 or less, and that all edges coming\
        out of a vertex will be given the same key/mask assignment.
    """

    def __init__(self):
        AbstractRoutingInfoAllocatorAlgorithm.__init__(self)

    def allocate_routing_info(self, subgraph, placements, n_keys_map):

        # check that this algorithm supports the constraints put onto the
        # partitioned_edges
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=subgraph.subedges,
            supported_constraints=self._supported_constraints,
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # take each subedge and create keys from its placement
        progress_bar = ProgressBar(len(subgraph.subvertices),
                                   "on allocating the key's and masks for"
                                   " each subedge")
        routing_infos = RoutingInfo()
        for subvert in subgraph.subvertices:
            out_going_subedges = subgraph.outgoing_subedges_from_subvertex(
                subvert)
            for out_going_subedge in out_going_subedges:
                n_keys = n_keys_map.n_keys_for_partitioned_edge(
                    out_going_subedge)
                if (n_keys > MAX_KEYS_SUPPORTED):
                    raise PacmanRouteInfoAllocationException(
                        "This routing info allocator can only support up to {}"
                        " keys for any given subedge; cannot therefore"
                        " allocate keys to {}, which is requesting {} keys"
                        .format(MAX_KEYS_SUPPORTED, out_going_subedge, n_keys))
                placement = placements.get_placement_of_subvertex(subvert)
                if placement is not None:
                    key = self._get_key_from_placement(placement)
                    keys_and_masks = list([KeyAndMask(key=key, mask=MASK)])
                    subedge_routing_info = SubedgeRoutingInfo(
                        keys_and_masks, out_going_subedge)
                    routing_infos.add_subedge_info(subedge_routing_info)
            progress_bar.update()
        progress_bar.end()
        return routing_infos

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
