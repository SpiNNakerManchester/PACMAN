"""
AbstractRoutingInfoAllocatorAlgorithm
"""

# pacman imports
from pacman.model.routing_tables.multicast_routing_table import \
    MulticastRoutingTable
from pacman.utilities import utility_calls
from pacman.exceptions import PacmanValueError
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_fixed_mask_constraint \
    import KeyAllocatorFixedMaskConstraint
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_fixed_key_and_mask_constraint \
    import KeyAllocatorFixedKeyAndMaskConstraint

# spinnmachine imports
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry


def get_edge_groups(partitioned_graph):
    """ Utility method to get groups of partitioned edges using any\
        :py:class:`pacman.model.constraints.key_allocator_same_key_constraint.KeyAllocatorSameKeyConstraint`\
        constraints.  Note that no checking is done here about conflicts\
        related to other constraints.
    """

    # Keep a dictionary of the group which contains an edge
    same_key_groups = list()
    for partitioned_vertex in partitioned_graph.subvertices:
        outgoing_edge_partitions = \
            partitioned_graph.outgoing_edges_partitions_from_vertex(
                partitioned_vertex)
        for partition_identifer in outgoing_edge_partitions:
            same_key_groups.append(
                outgoing_edge_partitions[partition_identifer].edges)
    return same_key_groups


def is_contiguous_range(same_key_group):
    """ Determine if any edge in the group has a\
        :py:class:`pacman.model.constraints.key_allocator_contiguous_range_constraint.KeyAllocatorContiguousRangeContraint`

    :param same_key_group: Set of partitioned edges that are to be\
                assigned the same keys and masks
    :type same_key_group: iterable of\
                :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
    :return: True if the range should be contiguous
    """
    for edge in same_key_group:
        constraints = utility_calls.locate_constraints_of_type(
            edge.constraints, KeyAllocatorContiguousRangeContraint)
        if len(constraints) > 0:
            return True
    return False


def get_fixed_mask(same_key_group):
    """ Get a fixed mask from a group of partitioned edges if a\
        :py:class:`pacman.model.constraints.key_allocator_same_key_constraint.KeyAllocatorFixedMaskConstraint`\
        constraint exists in any of the edges in the group.

    :param same_key_group: Set of partitioned edges that are to be\
                assigned the same keys and masks
    :type same_key_group: iterable of\
                :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
    :return: The fixed mask if found, or None
    :raise PacmanValueError: If two edges conflict in their requirements
    """
    mask = None
    fields = None
    edge_with_mask = None
    for edge in same_key_group:
        fixed_mask_constraints = utility_calls.locate_constraints_of_type(
            edge.constraints, KeyAllocatorFixedMaskConstraint)
        for fixed_mask_constraint in fixed_mask_constraints:
            if mask is not None and mask != fixed_mask_constraint.mask:
                raise PacmanValueError(
                    "Two Partitioned Edges {} and {} must have the same"
                    " key and mask, but have different fixed masks,"
                    " {} and {}".format(edge, edge_with_mask, mask,
                                        fixed_mask_constraint.mask))
            if (fields is not None and
                    fixed_mask_constraint.fields is not None and
                    fields != fixed_mask_constraint.fields):
                raise PacmanValueError(
                    "Two Partitioned Edges {} and {} must have the same"
                    " key and mask, but have different field ranges"
                    .format(edge, edge_with_mask))
            mask = fixed_mask_constraint.mask
            edge_with_mask = edge
            if fixed_mask_constraint.fields is not None:
                fields = fixed_mask_constraint.fields

    return mask, fields


def get_fixed_key_and_mask(same_key_group):
    """ Gets a fixed key and mask from a group of partitioned edges if a\
        :py:class:`pacman.model.constraints.key_allocator_same_key_constraint.KeyAllocatorFixedKeyAndMaskConstraint`\
        constraint exists in any of the edges in the group.

    :param same_key_group: Set of partitioned edges that are to be\
                assigned the same keys and masks
    :type same_key_group: iterable of\
                :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
    :raise PacmanValueError: If two edges conflict in their requirements
    """
    keys_and_masks = None
    edge_with_key_and_mask = None
    for edge in same_key_group:
        constraints = utility_calls.locate_constraints_of_type(
            edge.constraints, KeyAllocatorFixedKeyAndMaskConstraint)
        for constraint in constraints:

            # Check for conflicts
            if (keys_and_masks is not None and
                    keys_and_masks != constraint.keys_and_masks):
                raise PacmanValueError(
                    "Two Partitioned Edges {} and {} must have the same"
                    " key and mask, but have different fixed key and"
                    " masks, {} and {}".format(
                        edge, edge_with_key_and_mask, keys_and_masks,
                        constraint.keys_and_masks))
            keys_and_masks = constraint.keys_and_masks
            edge_with_key_and_mask = edge

    return keys_and_masks


def add_routing_key_entries(
        routing_paths, subedge_routing_info, out_going_subedge, routing_tables):
    """
    creates and adds entries for routing tables as required for the path
    :param routing_paths: the routing paths object generated from
    routing info
    :param subedge_routing_info: the subedge info object that contains keys
    :param out_going_subedge: the edge this is aossicated with
    :param routing_tables: the routing tables to adjust
    :return: None
    """
    path_entries = routing_paths.get_entries_for_edge(out_going_subedge)
    # iterate thoguh the entries in each path, adding a router entry if required
    for path_entry in path_entries:
        # locate the router
        router = routing_tables.get_routing_table_for_chip(
            path_entry.router_x, path_entry.router_y)
        if router is None:
            router = MulticastRoutingTable(
                path_entry.router_x, path_entry.router_y)
            routing_tables.add_routing_table(router)

        # add entries as required, or emrge them if entries alrteady exist
        for key_and_mask in subedge_routing_info.keys_and_masks:
            multicast_routing_entry = MulticastRoutingEntry(
                routing_entry_key=key_and_mask.key_combo,
                defaultable=path_entry.defaultable, mask=key_and_mask.mask,
                link_ids=path_entry.out_going_links,
                processor_ids=path_entry.out_going_processors)
            stored_entry = \
                router.get_multicast_routing_entry_by_routing_entry_key(
                    key_and_mask.key_combo, key_and_mask.mask)
            if stored_entry is None:
                router.add_mutlicast_routing_entry(MulticastRoutingEntry(
                    routing_entry_key=key_and_mask.key_combo,
                    defaultable=path_entry.defaultable,
                    mask=key_and_mask.mask,
                    link_ids=path_entry.out_going_links,
                    processor_ids=path_entry.out_going_processors))
            else:
                merged_entry = stored_entry.merge(multicast_routing_entry)
                router.remove_multicast_routing_entry(stored_entry)
                router.add_mutlicast_routing_entry(merged_entry)