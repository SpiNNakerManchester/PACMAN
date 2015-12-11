"""
AbstractRoutingInfoAllocatorAlgorithm
"""

# pacman imports
from pacman.model.constraints.key_allocator_constraints.key_allocator_fixed_field_constraint import \
    KeyAllocatorFixedFieldConstraint
from pacman.model.constraints.key_allocator_constraints.key_allocator_flexi_field_constraint import \
    KeyAllocatorFlexiFieldConstraint
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
from pacman import exceptions

# spinn_machine imports
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry

import logging
logger = logging.getLogger(__name__)


def get_edge_groups(partitioned_graph):
    """ Utility method to get groups of partitioned edges using any\
        :py:class:`pacman.model.constraints.key_allocator_same_key_constraint.KeyAllocatorSameKeyConstraint`\
        constraints.  Note that no checking is done here about conflicts\
        related to other constraints.
    :param partitioned_graph: the subgraph
    """

    # Keep a dictionary of the group which contains an edge
    fixed_key_groups = list()
    fixed_mask_groups = list()
    fixed_field_groups = list()
    flexi_field_groups = list()
    continious_groups = list()
    none_continious_groups = list()
    for partitioned_vertex in partitioned_graph.subvertices:
        outgoing_edge_partitions = \
            partitioned_graph.outgoing_edges_partitions_from_vertex(
                partitioned_vertex)
        for partition_id in outgoing_edge_partitions:
            partition = outgoing_edge_partitions[partition_id]
            # assume all edges have the same constraints in them. use first one
            # to deduce which group to place it into
            constraints = partition.constraints
            is_continious = False
            for constraint in constraints:
                if isinstance(constraint, KeyAllocatorFixedMaskConstraint):
                    fixed_mask_groups.append(partition)
                elif isinstance(constraint,
                                KeyAllocatorFixedKeyAndMaskConstraint):
                    fixed_key_groups.append(partition)
                elif isinstance(constraint, KeyAllocatorFlexiFieldConstraint):
                    flexi_field_groups.append(partition)
                elif isinstance(constraint, KeyAllocatorFixedFieldConstraint):
                    fixed_field_groups.append(partition)
                elif isinstance(constraint,
                                KeyAllocatorContiguousRangeContraint):
                    is_continious = True
                    continious_groups.append(partition)
            if not is_continious:
                none_continious_groups.append(partition)
    return (fixed_key_groups, fixed_mask_groups, fixed_field_groups,
            flexi_field_groups, continious_groups, none_continious_groups)


def check_n_keys_are_same_through_partition(partition_group, n_keys_map):
    """
    check that each edge in a partition has the same n_keys demands
    :param partition_group:
    :param n_keys_map:
    :return:
    """
    # Check how many keys are needed for the edges of the group
    edge_n_keys = None
    for edge in partition_group.edges:
        n_keys = n_keys_map.n_keys_for_partitioned_edge(edge)
        if edge_n_keys is None:
            edge_n_keys = n_keys
        elif edge_n_keys != n_keys:
            raise exceptions.PacmanRouteInfoAllocationException(
                "Two edges require the same keys but request a"
                " different number of keys")


def check_types_of_edge_constraint(sub_graph):
    """
    goes through the supgraph for opartitions and checks that the constraints
    are compatible.
    :param sub_graph: the subgraph to search throguh
    :return:
    """
    for partition in sub_graph.partitions:
        fixed_key = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedKeyAndMaskConstraint)

        fixed_mask = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedMaskConstraint)

        fixed_field = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedFieldConstraint)

        flexi_field = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFlexiFieldConstraint)

        if (len(fixed_key) > 1 or len(fixed_field) > 1
                or len(fixed_mask) > 1 or len(flexi_field) > 1):
            raise exceptions.PacmanConfigurationException(
                "There are more than one of the same constraint type on "
                "the partition {} for edges {}. Please fix and try again."
                .format(partition.identifer, partition.edges))

        fixed_key = len(fixed_key) == 1
        fixed_mask = len(fixed_mask) == 1
        fixed_field = len(fixed_field) == 1
        flexi_field = len(flexi_field) == 1

        # check for fixed key and a fixed mask. as these should have been
        # merged before now
        if fixed_key and fixed_mask:
            raise exceptions.PacmanConfigurationException(
                "The partition {} with edges {} has a fixed key and fixed "
                "mask constraint. These can be merged together, but is "
                "deemed an error here"
                    .format(partition.identifer, partition.edges))

        # check for a fixed key and fixed field, as these are incompatible
        if fixed_key and fixed_field:
            raise exceptions.PacmanConfigurationException(
                "The partition {} for edges {} has a fixed key and fixed "
                "field constraint. These may be mergeable together, but "
                "is deemed an error here"
                    .format(partition.identifer, partition.edges))

        # check that a fixed mask and fixed field have compatible masks
        if fixed_mask and fixed_field:
            _check_masks_are_correct(partition)

        # check that if theres a flexi field, and somet else, throw error
        if flexi_field and (fixed_mask or fixed_key or fixed_field):
            raise exceptions.PacmanConfigurationException(
                "The partition {} for edges {} has a flexi field and "
                "another fixed constraint. These maybe be mergeable, but "
                "is deemed an error here"
                .format(partition.identifer, partition.edges))


def _check_masks_are_correct(partition):
    """
    checks that the masks between a fixed mask constraint
    and a fixed_field constraint. completes if its correct, raises error
    otherwise
    :param partition: the outgoing_edge_partition to search for these
    constraints
    :return:
    """
    fixed_mask = \
        utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedMaskConstraint)[0]
    fixed_field = \
        utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedFieldConstraint)[0]
    mask = fixed_mask.mask
    for field in fixed_field.fields:
        if field.mask & mask != field.mask:
            raise exceptions.PacmanInvalidParameterException(
                "felid.mask, mask",
                "The field mask {} is outside of the mask {}"
                .format(field.mask, mask),
                "{}:{}".format(field.mask, mask))
        for other_field in fixed_field.fields:
            if (other_field != field and
                    other_field.mask & field.mask != 0):
                raise exceptions.PacmanInvalidParameterException(
                    "felid.mask, mask",
                    "Field masks {} and {} overlap".format(
                        field.mask, other_field.mask),
                    "{}:{}".format(field.mask, mask))


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


def add_routing_key_entries(
        routing_paths, subedge_routing_info, out_going_subedge,
        routing_tables):
    """
    creates and adds entries for routing tables as required for the path
    :param routing_paths: the routing paths object generated from routing info
    :param subedge_routing_info: the subedge info object that contains keys
    :param out_going_subedge: the edge this is associated with
    :param routing_tables: the routing tables to adjust
    :return: None
    """
    path_entries = routing_paths.get_entries_for_edge(out_going_subedge)

    # iterate through the entries in each path, adding a router entry if
    # required
    for path_entry in path_entries:

        # locate the router
        router = routing_tables.get_routing_table_for_chip(
            path_entry.router_x, path_entry.router_y)
        if router is None:
            router = MulticastRoutingTable(
                path_entry.router_x, path_entry.router_y)
            routing_tables.add_routing_table(router)

        # add entries as required, or merge them if entries already exist
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
