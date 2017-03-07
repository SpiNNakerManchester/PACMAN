from spinn_utilities.progress_bar import ProgressBar

# pacman imports
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.partition_routing_info \
    import PartitionRoutingInfo
from pacman.utilities import utility_calls
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.constraints.key_allocator_constraints\
    .abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint\
    import KeyAllocatorContiguousRangeContraint

MAX_KEYS_SUPPORTED = 2048
MASK = 0xFFFFF800


class BasicRoutingInfoAllocator(object):
    """ An basic algorithm that can produce routing keys and masks for\
        edges in a graph based on the x,y,p of the placement\
        of the preceding vertex.
        Note that no constraints are supported, and that the number of keys\
        required by each edge must be 2048 or less, and that all edges coming\
        out of a vertex will be given the same key/mask assignment.
    """

    __slots__ = []

    def __call__(self, machine_graph, placements, n_keys_map):
        """

        :param machine_graph:\
            The machine graph to allocate the routing info for
        :type machine_graph:\
            :py:class:`pacman.model.graph.machine.machine_graph.MachineGraph`
        :param placements: The placements of the vertices
        :type placements:\
            :py:class:`pacman.model.placements.placements.Placements`
        :param n_keys_map:\
            A map between the edges and the number of keys required by the\
            edges
        :type n_keys_map:\
            :py:class:`pacman.model.routing_info.abstract_machine_partition_n_keys_map.AbstractMachinePartitionNKeysMap`
        :return: The routing information
        :rtype:\
            :py:class:`pacman.model.routing_info.partition_routing_info.PartitionRoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: If\
                   something goes wrong with the allocation
        """

        # check that this algorithm supports the constraints put onto the
        # partitions
        supported_constraints = [
            KeyAllocatorContiguousRangeContraint]
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=supported_constraints,
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # take each edge and create keys from its placement
        progress_bar = ProgressBar(
            machine_graph.n_vertices, "Allocating routing keys")
        routing_infos = RoutingInfo()
        for vertex in machine_graph.vertices:
            partitions = machine_graph.\
                get_outgoing_edge_partitions_starting_at_vertex(vertex)
            for partition in partitions:
                n_keys = n_keys_map.n_keys_for_partition(partition)
                if n_keys > MAX_KEYS_SUPPORTED:
                    raise PacmanRouteInfoAllocationException(
                        "This routing info allocator can only support up to {}"
                        " keys for any given edge; cannot therefore"
                        " allocate keys to {}, which is requesting {} keys"
                        .format(MAX_KEYS_SUPPORTED, partition, n_keys))
                placement = placements.get_placement_of_vertex(vertex)
                if placement is not None:
                    key = self._get_key_from_placement(placement)
                    keys_and_masks = list([BaseKeyAndMask(base_key=key,
                                                          mask=MASK)])
                    routing_info = PartitionRoutingInfo(
                        keys_and_masks, partition)
                    routing_infos.add_partition_info(routing_info)
                else:
                    raise PacmanRouteInfoAllocationException(
                        "The vertex '{}' has no placement".format(vertex))

            progress_bar.update()
        progress_bar.end()

        return routing_infos

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
