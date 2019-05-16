import math
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_info import (
    RoutingInfo, PartitionRoutingInfo, BaseKeyAndMask)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints)
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.model.constraints.key_allocator_constraints import (
    AbstractKeyAllocatorConstraint, ContiguousKeyRangeContraint)
from pacman.model.graphs.common import EdgeTrafficType

KEY_SIZE = 32


class ZonedRoutingInfoAllocator(object):
    """ An basic algorithm that can produce routing keys and masks for\
        edges in a graph based on the x,y,p of the placement\
        of the preceding vertex.

    .. note::
        No constraints are supported, and that the number of keys\
        required by each edge must be 2048 or less, and that all edges coming\
        out of a vertex will be given the same key/mask assignment.
    """

    __slots__ = []

    def __call__(self, application_graph, graph_mapper, machine_graph,
                 placements, n_keys_map):
        """
        :param machine_graph:\
            The machine graph to allocate the routing info for
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param placements: The placements of the vertices
        :type placements:\
            :py:class:`pacman.model.placements.placements.Placements`
        :param n_keys_map:\
            A map between the edges and the number of keys required by the\
            edges
        :type n_keys_map:\
            :py:class:`pacman.model.routing_info.AbstractMachinePartitionNKeysMap`
        :return: The routing information
        :rtype:\
            :py:class:`pacman.model.routing_info.PartitionRoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: \
            If something goes wrong with the allocation
        """

        # check that this algorithm supports the constraints put onto the
        # partitions
        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[ContiguousKeyRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        progress = ProgressBar(
            application_graph.n_vertices, "Calculating zones")
        max_machine = 0
        max_partition = 0
        max_keys = 0
        for app_vertex in progress.over(application_graph.vertices):
            machine_vertices = graph_mapper.get_machine_vertices(app_vertex)
            max_machine = max(max_machine, len(machine_vertices))
            for vertex in machine_vertices:
                partitions = machine_graph.\
                    get_outgoing_edge_partitions_starting_at_vertex(vertex)
                # Do we need to check type here
                max_partition = max(max_partition, len(partitions))
                for partition in partitions:
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        n_keys = n_keys_map.n_keys_for_partition(partition)
                        max_keys = max(max_keys, n_keys)

        application_bites = self.bites_needed(application_graph.n_vertices)
        machine_bites = self.bites_needed(max_machine)
        partition_bites = self.bites_needed(max_partition)
        key_bites = self.bites_needed(max_keys)
        machine_shift = key_bites + partition_bites
        app_shift = application_bites + machine_shift

        if application_bites + machine_bites + partition_bites + key_bites \
                > KEY_SIZE:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} + {} + {}  bites"
                "".format(application_bites, machine_bites, partition_bites,
                          key_bites))

        mask = 2**32 - 2**key_bites

        # take each edge and create keys from its placement
        progress = ProgressBar(
            application_graph.n_vertices, "Allocating routing keys")
        routing_infos = RoutingInfo()

        app_index = 0
        for app_vertex in application_graph.vertices:
            machine_vertices = graph_mapper.get_machine_vertices(app_vertex)
            max_machine = max(max_machine, len(machine_vertices))
            for machine_index, vertex in enumerate(machine_vertices):
                partitions = machine_graph. \
                    get_outgoing_edge_partitions_starting_at_vertex(vertex)
                # Do we need to check type here
                max_partition = max(max_partition, len(partitions))
                for partition_index, partition in enumerate(partitions):
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        key = app_index << app_shift | \
                              machine_index << machine_shift | \
                              partition_index << key_bites
                        keys_and_masks = list([BaseKeyAndMask(
                            base_key=key, mask=mask)])
                        info = PartitionRoutingInfo(keys_and_masks, partition)
                        routing_infos.add_partition_info(info)
            app_index += 1

        return routing_infos

    def bites_needed(self, size):
        return math.ceil(math.log(size, 2))
