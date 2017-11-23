# pacman imports

from enum import Enum

from pacman.model.constraints.key_allocator_constraints\
    import FixedKeyFieldConstraint, FlexiKeyFieldConstraint
from pacman.model.constraints.key_allocator_constraints\
    import ContiguousKeyRangeContraint
from pacman.model.constraints.key_allocator_constraints\
    import FixedMaskConstraint
from pacman.model.constraints.key_allocator_constraints\
    import FixedKeyAndMaskConstraint
from pacman.model.constraints.key_allocator_constraints.\
    share_key_constraint import \
    ShareKeyConstraint
from pacman.utilities import utility_calls
from pacman.exceptions import (PacmanValueError, PacmanConfigurationException,
                               PacmanInvalidParameterException)
from spinn_utilities.ordered_set import OrderedSet

import logging
logger = logging.getLogger(__name__)

SHARE_KEY_FLAGS = Enum(
    value="SHAKE_KEY_FLAGS",
    names=[
        ("PLAIN", 0),
        ("FIXED_KEY", 1),
        ("FIXED_MASK", 2),
        ("FIXED_FIELD", 3),
        ("FLEXI_FIELD", 4)])

def get_edge_groups(machine_graph, traffic_type):
    """ Utility method to get groups of edges using any\
        :py:class:`pacman.model.constraints.key_allocator_constraints.KeyAllocatorSameKeyConstraint`\
        constraints.  Note that no checking is done here about conflicts\
        related to other constraints.

    :param machine_graph: the machine graph
    :param traffic_type: the traffic type to group
    """

    # Keep a dictionary of the group which contains an edge
    fixed_key_groups = list()
    shared_key_groups = list()
    fixed_mask_groups = list()
    fixed_field_groups = list()
    flexi_field_groups = list()
    continuous_groups = OrderedSet()
    none_continuous_groups = OrderedSet()

    share_key_mappings = dict()

    for vertex in machine_graph.vertices:
        for partition in machine_graph.\
                get_outgoing_edge_partitions_starting_at_vertex(vertex):

            # only process partitions of the correct traffic type
            if partition.traffic_type == traffic_type:

                # assume all edges have the same constraints in them. use \
                # first one to deduce which group to place it into
                constraints = partition.constraints

                # get types of constraints from this partition
                is_continuous, is_fixed_mask, is_fixed_key, is_flexi_field, \
                    is_fixed_field, is_shared_key, n_set = \
                    _check_types_of_constraints(constraints)

                # place in correct continuous block
                if is_continuous:
                    continuous_groups.add(partition)
                else:
                    none_continuous_groups.add(partition)

                # process the partition into the correct fields
                _process_partition(
                    fixed_key_groups, shared_key_groups, fixed_mask_groups,
                    fixed_field_groups, flexi_field_groups, is_fixed_mask,
                    is_fixed_key, is_flexi_field, is_fixed_field,
                    is_shared_key, n_set, partition, share_key_mappings)

    # return the set of groups
    return (fixed_key_groups, shared_key_groups,
            fixed_mask_groups, fixed_field_groups, flexi_field_groups,
            continuous_groups, none_continuous_groups)


def _process_partition(
        fixed_key_groups, shared_key_groups, fixed_mask_groups,
        fixed_field_groups, flexi_field_groups, is_fixed_mask,
        is_fixed_key, is_flexi_field, is_fixed_field,
        is_shared_key, n_set, partition, share_key_mappings):

    # this partition already in a share key somewhere, merge in
    if partition in share_key_mappings:

        # locate previous referral
        tracked_set, other_constraint = share_key_mappings[partition]

        # if share key, locate and find partitions to merge
        if is_shared_key:

            # get share key constraint that must be there
            share_key_constraint = \
                utility_calls.locate_first_constraint_of_type(
                    partition.constraints, ShareKeyConstraint)

            # search for merging groups
            _search_for_merger(
                share_key_constraint, partition, share_key_mappings,
                tracked_set, fixed_key_groups, fixed_mask_groups,
                fixed_field_groups, flexi_field_groups, is_fixed_mask,
                is_fixed_key, is_flexi_field, is_fixed_field,
                shared_key_groups, is_shared_key)

            # verify constraints are correct
            _verify_constraints(
                partition, is_fixed_mask, is_fixed_key,
                is_flexi_field, is_fixed_field, tracked_set)
        else:  # need to check constraint matching
            _verify_constraints(partition, is_fixed_mask, is_fixed_key,
                                is_flexi_field, is_fixed_field, tracked_set)

    else:  # not in a share key already. explore its own components
        if is_shared_key:  # if is share key, look for any already in existence

            # get share key
            share_key_constraint = \
                utility_calls.locate_first_constraint_of_type(
                    partition.constraints, ShareKeyConstraint)

            # search for merger
            tracked_set = _search_for_merger(
                share_key_constraint, partition, share_key_mappings, None,
                fixed_key_groups, fixed_mask_groups, fixed_field_groups,
                flexi_field_groups, is_fixed_mask, is_fixed_key,
                is_flexi_field, is_fixed_field, shared_key_groups,
                is_shared_key)

            # verify the constraints of the tracked set
            _verify_constraints(partition, is_fixed_mask, is_fixed_key,
                                is_flexi_field, is_fixed_field, tracked_set)

        else:  # no share, not already in, so just add as new one
            _linked_shared_constraints(
                fixed_key_groups, fixed_mask_groups, fixed_field_groups,
                flexi_field_groups, is_fixed_mask, is_fixed_key,
                is_flexi_field, is_fixed_field, partition, share_key_mappings,
                shared_key_groups, is_shared_key)


def _search_for_merger(
        share_key_constraint, partition, share_key_mappings, tracked_set,
        fixed_key_groups, fixed_mask_groups, fixed_field_groups,
        flexi_field_groups, is_fixed_mask, is_fixed_key,
        is_flexi_field, is_fixed_field, shared_key_groups, is_shared_key):

    found_track_list = tracked_set
    found_other_constraint = None

    # locate merge-able track list partition
    for other_partition in share_key_constraint.other_partitions:
        # check that no merger
        if other_partition in share_key_mappings:

            # get other mapped version
            other_track_list, found_other_constraint = \
                share_key_mappings[other_partition]


            if found_track_list is None:
                other_track_list.add(partition)
                share_key_mappings[partition] = other_track_list
                found_track_list = other_track_list
                _verify_constraints(
                    partition, is_fixed_mask, is_fixed_key,
                    is_flexi_field, is_fixed_field, found_track_list)
            else:
                found_track_list.update(other_track_list)
                for partition in other_track_list:
                    share_key_mappings[]








    if found_track_list is None and found_other_constraint is None:
        _linked_shared_constraints(
            fixed_key_groups, fixed_mask_groups, fixed_field_groups,
            flexi_field_groups, is_fixed_mask, is_fixed_key,
            is_flexi_field, is_fixed_field, partition,
            share_key_mappings, shared_key_groups, is_shared_key)

    share_key_mappings[other_partition] = tracked_set

        # if merger found
        if partition in share_key_mappings:
            found_track_list, found_other_constraint = \
                share_key_mappings[partition]

    if found_track_list is None and found_other_constraint is None:
        _linked_shared_constraints(
            fixed_key_groups, fixed_mask_groups, fixed_field_groups,
            flexi_field_groups, is_fixed_mask, is_fixed_key,
            is_flexi_field, is_fixed_field, partition,
            share_key_mappings, shared_key_groups)


def _verify_constraints(partition, is_fixed_mask, is_fixed_key,
                        is_flexi_field, is_fixed_field, tracked_set):
    constraint = None
    valid = None
    if is_fixed_key:
        valid = _search_for_failed_mix_of_constraints(
            FixedKeyAndMaskConstraint, tracked_set)
    if is_fixed_mask:
        valid = _search_for_failed_mix_of_constraints(
            FixedMaskConstraint, tracked_set)
    if is_flexi_field:
        valid = _search_for_failed_mix_of_constraints(
            FlexiKeyFieldConstraint, tracked_set)
    if is_fixed_field:
        valid = _search_for_failed_mix_of_constraints(
            FixedKeyFieldConstraint, tracked_set)
    if not valid:
        raise Exception(
            "The merger of {} into the set {} failed as constraint {} is not "
            "compatible with the set".format(
                partition, tracked_set, constraint))


def _search_for_failed_mix_of_constraints(constraint_type, set_of_partitions):
    constraint_to_test_against = utility_calls.locate_first_constraint_of_type(
        set_of_partitions.peek().constraints, constraint_type)

    for partition in set_of_partitions:
        other_constraint = utility_calls.locate_first_constraint_of_type(
            partition.constraints, constraint_type)
        if constraint_to_test_against != other_constraint:
            return False
    return True


def _linked_shared_constraints(
        fixed_key_groups, fixed_mask_groups, fixed_field_groups,
        flexi_field_groups, is_fixed_mask, is_fixed_key, is_flexi_field,
        is_fixed_field, partition, shared_key_mappings, shared_key_groups,
        is_shared_key):
    new_set = OrderedSet()
    new_set.add(partition)
    shared_key_mappings[partition] = new_set

    if is_fixed_key:
        fixed_key_groups.append(new_set)
    if is_fixed_mask:
        fixed_mask_groups.add(new_set)
    if is_flexi_field:
        flexi_field_groups.add(new_set)
    if is_fixed_field:
        fixed_field_groups.add(new_set)
    if is_shared_key:
        shared_key_groups.add(new_set)

def _check_types_of_constraints(constraints):
    is_continuous = False
    is_fixed_mask = False
    is_fixed_key = False
    is_flexi_field = False
    is_fixed_field = False
    is_shared_key = False

    # locate types of constraints to consider
    for constraint in constraints:
        if isinstance(constraint, FixedMaskConstraint):
            is_fixed_mask = True
        elif isinstance(constraint, FixedKeyAndMaskConstraint):
            is_fixed_key = True
        elif isinstance(constraint, FlexiKeyFieldConstraint):
            is_flexi_field = True
        elif isinstance(constraint, FixedKeyFieldConstraint):
            is_fixed_field = True
        elif isinstance(constraint, ContiguousKeyRangeContraint):
            is_continuous = True
        elif isinstance(constraint, ShareKeyConstraint):
            is_shared_key = True

    # find how many are set
    n_set = 0
    for check in [is_continuous, is_fixed_mask, is_fixed_key,
                  is_flexi_field, is_fixed_field, is_shared_key]:
        if check:
            n_set += 1

    return is_continuous, is_fixed_mask, is_fixed_key, is_flexi_field, \
        is_fixed_field, is_shared_key, n_set


def check_types_of_edge_constraint(machine_graph):
    """ Go through the graph for operations and checks that the constraints\
        are compatible.

    :param machine_graph: the graph to search through
    :rtype: None:
    """
    for partition in machine_graph.outgoing_edge_partitions:
        fixed_key = utility_calls.locate_constraints_of_type(
            partition.constraints, FixedKeyAndMaskConstraint)

        fixed_mask = utility_calls.locate_constraints_of_type(
            partition.constraints, FixedMaskConstraint)

        fixed_field = utility_calls.locate_constraints_of_type(
            partition.constraints, FixedKeyFieldConstraint)

        flexi_field = utility_calls.locate_constraints_of_type(
            partition.constraints, FlexiKeyFieldConstraint)

        if (len(fixed_key) > 1 or len(fixed_field) > 1 or
                len(fixed_mask) > 1 or len(flexi_field) > 1):
            raise PacmanConfigurationException(
                "There are more than one of the same constraint type on "
                "the partition {} starting at {}. Please fix and try again."
                .format(partition.identifer, partition.pre_vertex))

        fixed_key = len(fixed_key) == 1
        fixed_mask = len(fixed_mask) == 1
        fixed_field = len(fixed_field) == 1
        flexi_field = len(flexi_field) == 1

        # check for fixed key and a fixed mask. as these should have been
        # merged before now
        if fixed_key and fixed_mask:
            raise PacmanConfigurationException(
                "The partition {} starting at {} has a fixed key and fixed "
                "mask constraint. These can be merged together, but is "
                "deemed an error here"
                .format(partition.identifer, partition.pre_vertex))

        # check for a fixed key and fixed field, as these are incompatible
        if fixed_key and fixed_field:
            raise PacmanConfigurationException(
                "The partition {} starting at {} has a fixed key and fixed "
                "field constraint. These may be merge-able together, but "
                "is deemed an error here"
                .format(partition.identifer, partition.pre_vertex))

        # check that a fixed mask and fixed field have compatible masks
        if fixed_mask and fixed_field:
            _check_masks_are_correct(partition)

        # check that if there's a flexible field, and something else, throw
        # error
        if flexi_field and (fixed_mask or fixed_key or fixed_field):
            raise PacmanConfigurationException(
                "The partition {} starting at {} has a flexible field and "
                "another fixed constraint. These maybe be merge-able, but "
                "is deemed an error here"
                .format(partition.identifer, partition.pre_vertex))


def _check_masks_are_correct(partition):
    """ Check that the masks between a fixed mask constraint\
        and a fixed_field constraint. completes if its correct, raises error\
        otherwise

    :param partition: the outgoing_edge_partition to search for these\
                constraints
    :rtype: None:
    """
    fixed_mask = utility_calls.locate_constraints_of_type(
        partition.constraints, FixedMaskConstraint)[0]
    fixed_field = utility_calls.locate_constraints_of_type(
        partition.constraints, FixedKeyFieldConstraint)[0]
    mask = fixed_mask.mask
    for field in fixed_field.fields:
        if field.mask & mask != field.mask:
            raise PacmanInvalidParameterException(
                "field.mask, mask",
                "The field mask {} is outside of the mask {}".format(
                    field.mask, mask),
                "{}:{}".format(field.mask, mask))
        for other_field in fixed_field.fields:
            if (other_field != field and
                    other_field.mask & field.mask != 0):
                raise PacmanInvalidParameterException(
                    "field.mask, mask",
                    "Field masks {} and {} overlap".format(
                        field.mask, other_field.mask),
                    "{}:{}".format(field.mask, mask))


def get_fixed_mask(same_key_group):
    """ Get a fixed mask from a group of edges if a\
        :py:class:`pacman.model.constraints.key_allocator_constraints.FixedMaskConstraint`\
        constraint exists in any of the edges in the group.

    :param same_key_group: Set of edges that are to be\
                assigned the same keys and masks
    :type same_key_group: iterable of\
        :py:class:`pacman.model.graph.machine.MachineEdge`
    :return: The fixed mask if found, or None
    :raise PacmanValueError: If two edges conflict in their requirements
    """
    mask = None
    fields = None
    edge_with_mask = None
    for edge in same_key_group:
        fixed_mask_constraints = utility_calls.locate_constraints_of_type(
            edge.constraints, FixedMaskConstraint)
        for fixed_mask_constraint in fixed_mask_constraints:
            if mask is not None and mask != fixed_mask_constraint.mask:
                raise PacmanValueError(
                    "Two Edges {} and {} must have the same"
                    " key and mask, but have different fixed masks,"
                    " {} and {}".format(edge, edge_with_mask, mask,
                                        fixed_mask_constraint.mask))
            if (fields is not None and
                    fixed_mask_constraint.fields is not None and
                    fields != fixed_mask_constraint.fields):
                raise PacmanValueError(
                    "Two Edges {} and {} must have the same"
                    " key and mask, but have different field ranges"
                    .format(edge, edge_with_mask))
            mask = fixed_mask_constraint.mask
            edge_with_mask = edge
            if fixed_mask_constraint.fields is not None:
                fields = fixed_mask_constraint.fields

    return mask, fields
