from pacman.model.constraints.abstract_constraints\
    .abstract_key_allocator_constraint import \
    AbstractKeyAllocatorConstraint
from pacman.model.data_request_interfaces\
    .abstract_requires_routing_info_partitioned_vertex import \
    RequiresRoutingInfoPartitionedVertex
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
from pacman.utilities import utility_calls
from pacman.utilities.utility_objs.progress_bar import ProgressBar
from pacman import exceptions
from pacman.utilities.algorithm_utilities import \
    routing_info_allocator_utilities


class DestinationBasedRoutingInfoAllocator(object):
    """ An algorithm that can produce routing keys and masks for\
        edges in a partitioned_graph based on the x,y,p of the placement\
        of the receiving partitioned vertex.
        Note that no constraints are supported, and that the number of keys\
        required by each edge must be 2048 or less, and that all edges coming\
        out of a vertex going to the same destination need to reside\
        in the same partition.
    """

    MAX_KEYS_SUPPORTED = 2048
    MASK = 0xFFFFF800

    def __call__(self, subgraph, placements, n_keys_map, routing_paths):
        """
        Allocates routing information to the partitioned edges in a\
        partitioned graph

        :param subgraph: The partitioned graph to allocate the routing info for
        :type subgraph:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph`
        :param placements: The placements of the subvertices
        :type placements:\
                    :py:class:`pacman.model.placements.placements.Placements`
        :param n_keys_map: A map between the partitioned edges and the number\
                    of keys required by the edges
        :type n_keys_map:\
                    :py:class:`pacman.model.routing_info.abstract_partitioned_edge_n_keys_map.AbstractPartitionedEdgeNKeysMap`
        :param routing_paths: the paths each partitioned edge takes to get\
                from source to destination.
        :type routing_paths:
            :py:class:`pacman.model.routing_paths.multicast_routing_paths.MulticastRoutingPaths
        :return: The routing information
        :rtype: :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`,
                :py:class:`pacman.model.routing_tables.multicast_routing_table.MulticastRoutingTable
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: If\
                   something goes wrong with the allocation
        """

        # check that this algorithm supports the constraints put onto the
        # partitioned_edges
        supported_constraints = [RequiresRoutingInfoPartitionedVertex]
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=subgraph.subedges,
            supported_constraints=supported_constraints,
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # take each subedge and create keys from its placement
        progress_bar = ProgressBar(len(subgraph.subedges),
                                   "Allocating routing keys")
        routing_infos = RoutingInfo()
        routing_tables = MulticastRoutingTables()

        for subedge in subgraph.subedges:
            destination = subedge.post_subvertex
            placement = placements.get_placement_of_subvertex(destination)
            key = self._get_key_from_placement(placement)
            keys_and_masks = list([BaseKeyAndMask(base_key=key,
                                                  mask=self.MASK)])
            n_keys = n_keys_map.n_keys_for_partitioned_edge(subedge)
            if n_keys > self.MAX_KEYS_SUPPORTED:
                raise exceptions.PacmanConfigurationException(
                    "Only edges which require less than {} keys are supported"
                    .format(self.MAX_KEYS_SUPPORTED))

            subedge_info = SubedgeRoutingInfo(keys_and_masks, subedge)
            routing_infos.add_subedge_info(subedge_info)

            # update routing tables with entries
            routing_info_allocator_utilities.add_routing_key_entries(
                routing_paths, subedge_info, subedge, routing_tables)
            progress_bar.update()
        progress_bar.end()

        return {'routing_infos': routing_infos,
                'routing_tables': routing_tables}

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
