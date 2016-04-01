
# pacman imports
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.partition_routing_info \
    import PartitionRoutingInfo
from pacman.utilities import utility_calls
from spinn_machine.utilities.progress_bar import ProgressBar
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.constraints.abstract_constraints\
    .abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint\
    import KeyAllocatorContiguousRangeContraint

MAX_KEYS_SUPPORTED = 2048
MASK = 0xFFFFF800


class BasicRoutingInfoAllocator(object):
    """ An basic algorithm that can produce routing keys and masks for\
        edges in a partitioned_graph based on the x,y,p of the placement\
        of the preceding partitioned vertex.
        Note that no constraints are supported, and that the number of keys\
        required by each edge must be 2048 or less, and that all edges coming\
        out of a vertex will be given the same key/mask assignment.
    """

    def __call__(self, partitioned_graph, placements, n_keys_map):
        """
        Allocates routing information to the partitioned edges in a\
        partitioned graph

        :param partitioned_graph: The partitioned graph to allocate the \
                    outing info for
        :type partitioned_graph:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph`
        :param placements: The placements of the subvertices
        :type placements:\
                    :py:class:`pacman.model.placements.placements.Placements`
        :param n_keys_map: A map between the partitioned edges and the number\
                    of keys required by the edges
        :type n_keys_map:\
                    :py:class:`pacman.model.routing_info.abstract_partitioned_edge_n_keys_map.AbstractPartitionedEdgeNKeysMap`
        :return: The routing information
        :rtype: :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`,
                :py:class:`pacman.model.routing_tables.multicast_routing_table.MulticastRoutingTable
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: If\
                   something goes wrong with the allocation
        """

        # check that this algorithm supports the constraints put onto the
        # partitioned_edges
        supported_constraints = [
            KeyAllocatorContiguousRangeContraint]
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=partitioned_graph.partitions,
            supported_constraints=supported_constraints,
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # take each subedge and create keys from its placement
        progress_bar = ProgressBar(len(partitioned_graph.subvertices),
                                   "Allocating routing keys")
        routing_infos = RoutingInfo()
        for subvert in partitioned_graph.subvertices:
            partitions = partitioned_graph.\
                outgoing_edges_partitions_from_vertex(subvert)
            for partition in partitions.values():
                n_keys = n_keys_map.n_keys_for_partition(partition)
                if n_keys > MAX_KEYS_SUPPORTED:
                    raise PacmanRouteInfoAllocationException(
                        "This routing info allocator can only support up to {}"
                        " keys for any given subedge; cannot therefore"
                        " allocate keys to {}, which is requesting {} keys"
                        .format(MAX_KEYS_SUPPORTED, partition, n_keys))
                placement = placements.get_placement_of_subvertex(subvert)
                if placement is not None:
                    key = self._get_key_from_placement(placement)
                    keys_and_masks = list([BaseKeyAndMask(base_key=key,
                                                          mask=MASK)])
                    subedge_routing_info = PartitionRoutingInfo(
                        keys_and_masks, partition)
                    routing_infos.add_partition_info(subedge_routing_info)
                else:
                    raise PacmanRouteInfoAllocationException(
                        "This subvertex '{}' has no placement! this should "
                        "never occur, please fix and try again."
                        .format(subvert))

            progress_bar.update()
        progress_bar.end()

        return {'routing_infos': routing_infos}

    @staticmethod
    def _get_key_from_placement(placement):
        """ Return a key given a placement

        :param placement: the associated placement
        :type placement:\
                    :py:class:`pacman.model.placements.placement.Placement`
        :return: The key
        :rtype: int
        """
        return placement.x << 24 | placement.y << 16 | placement.p << 11
