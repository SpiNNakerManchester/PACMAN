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


class LabeledList(list):
    def __init__(self, label):
        self._label = label
        list.__init__(self)

    def __repr__(self):
        return self._label + list.__repr__(self)


def get_edge_groups(machine_graph, traffic_type):
    """ Utility method to get groups of edges using any\
        :py:class:`pacman.model.constraints.key_allocator_constraints.KeyAllocatorSameKeyConstraint`\
        constraints.  Note that no checking is done here about conflicts\
        related to other constraints.

    :param machine_graph: the machine graph
    :param traffic_type: the traffic type to group
    """

    # Keep a dictionary of the group which contains an edge
    fixed_key_groups = LabeledList("fixed_key")
    shared_key_groups = LabeledList("share_key")
    fixed_mask_groups = LabeledList("fixed_mask")
    fixed_field_groups = LabeledList("fixed_field")
    flexi_field_groups = LabeledList("flexi_field")
    continuous_groups = LabeledList("continious")
    none_continuous_groups = LabeledList("none_continious")

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
                    is_fixed_field, is_shared_key = \
                    _check_types_of_constraints(constraints)

                # process the partition into the correct fields
                _process_partition(
                    fixed_key_groups, shared_key_groups,
                    fixed_mask_groups,
                    fixed_field_groups, flexi_field_groups, continuous_groups,
                    none_continuous_groups, is_fixed_mask,
                    is_fixed_key, is_flexi_field, is_fixed_field,
                    is_shared_key, is_continuous, partition, share_key_mappings)

    # return the set of groups
    return (fixed_key_groups, shared_key_groups,
            fixed_mask_groups, fixed_field_groups, flexi_field_groups,
            continuous_groups, none_continuous_groups)


def _process_partition(
        fixed_key_groups, shared_key_groups, fixed_mask_groups,
        fixed_field_groups, flexi_field_groups, continuous_groups,
        none_continuous_groups, is_fixed_mask,
        is_fixed_key, is_flexi_field, is_fixed_field,
        is_shared_key, is_continuous, partition, share_key_mappings):

    # this partition already in a share key somewhere, merge in
    if partition in share_key_mappings:

        # locate previous referral
        tracked_set, group = share_key_mappings[partition]

        if group == shared_key_groups and not is_shared_key:
            _, group = _linked_shared_constraints(
                fixed_key_groups, fixed_mask_groups, fixed_field_groups,
                flexi_field_groups, continuous_groups,
                none_continuous_groups, is_fixed_mask, is_fixed_key,
                is_flexi_field, is_fixed_field, partition, share_key_mappings,
                shared_key_groups, is_shared_key, is_continuous)

        # if share key, locate and find partitions to merge
        if is_shared_key:
            # get share key constraint that must be there
            other_partitions = \
                utility_calls.locate_first_constraint_of_type(
                    partition.constraints, ShareKeyConstraint).other_partitions
        else:
            other_partitions = tracked_set

        # search for merging groups
        _search_for_merger(
            other_partitions, partition,
            share_key_mappings, tracked_set, group, fixed_key_groups,
            fixed_mask_groups, fixed_field_groups, flexi_field_groups,
            continuous_groups, none_continuous_groups, is_fixed_mask,
            is_fixed_key, is_flexi_field, is_fixed_field,
            shared_key_groups, is_shared_key, is_continuous)

        # verify constraints are correct
        _verify_constraints(
            partition, is_fixed_mask, is_fixed_key, is_flexi_field,
            is_fixed_field, is_shared_key, is_continuous, tracked_set)

    else:  # not in a share key already. explore its own components
        if is_shared_key:  # if is share key, look for any already in existence

            # get share key
            other_partitions = \
                utility_calls.locate_first_constraint_of_type(
                    partition.constraints, ShareKeyConstraint).other_partitions
            new_set = OrderedSet()
            new_set.add(partition)
            shared_key_groups.append(new_set)
            share_key_mappings[partition] = (new_set, shared_key_groups)

            # search for merger
            tracked_set = _search_for_merger(
                other_partitions, partition,
                share_key_mappings, new_set, shared_key_groups,
                fixed_key_groups, fixed_mask_groups, fixed_field_groups,
                flexi_field_groups, continuous_groups,
                none_continuous_groups, is_fixed_mask, is_fixed_key,
                is_flexi_field, is_fixed_field, shared_key_groups,
                is_shared_key, is_continuous)
        else:  # no share, not already in, so just add as new one
            tracked_set, _ = _linked_shared_constraints(
                fixed_key_groups, fixed_mask_groups, fixed_field_groups,
                flexi_field_groups, continuous_groups,
                none_continuous_groups, is_fixed_mask, is_fixed_key,
                is_flexi_field, is_fixed_field, partition, share_key_mappings,
                shared_key_groups, is_shared_key, is_continuous)

        # verify the constraints of the tracked set
        _verify_constraints(
            partition, is_fixed_mask, is_fixed_key, is_flexi_field,
            is_fixed_field, is_shared_key, is_continuous, tracked_set)


def _search_for_merger(
        other_partitions, partition, share_key_mappings, found_track_list,
        group, fixed_key_groups, fixed_mask_groups, fixed_field_groups,
        flexi_field_groups, continuous_groups, none_continuous_groups,
        is_fixed_mask, is_fixed_key, is_flexi_field,
        is_fixed_field, shared_key_groups, is_shared_key, is_continuous):

    # locate merge-able track list partition
    for other_partition in other_partitions:
        # check that no merger
        if other_partition in share_key_mappings:

            # get other mapped version
            other_track_list, other_group = \
                share_key_mappings[other_partition]

            if found_track_list is None:  # im not in, but my mix is
                other_track_list.add(partition)
                share_key_mappings[partition] = (other_track_list, other_group)
                found_track_list = other_track_list
                _verify_constraints(
                    partition, is_fixed_mask, is_fixed_key,
                    is_flexi_field, is_fixed_field, is_shared_key,
                    is_continuous, found_track_list)

            else:  # is in and is share key

                # merge the other into me, as i am placed
                if found_track_list != other_track_list:
                    found_track_list.update(other_track_list)

                    # remove mapping for other set, as now its in my set
                    other_group.remove(other_track_list)

                    # update partition to set mapping
                    for other_track_list_partition in other_track_list:
                        share_key_mappings[other_track_list_partition] = \
                            (found_track_list, group)

                    # check all constraints match again
                    _verify_constraints(
                        partition, is_fixed_mask, is_fixed_key,
                        is_flexi_field, is_fixed_field, is_shared_key,
                        is_continuous, found_track_list)
        else:
            if partition != other_partition:
                found_track_list.add(other_partition)
                share_key_mappings[other_partition] = (found_track_list, group)

    return found_track_list


def _verify_constraints(
        partition, is_fixed_mask, is_fixed_key, is_flexi_field, is_fixed_field,
        is_share_key, is_continious, tracked_set):
    constraint = None
    valid = None
    if is_fixed_key:
        valid = _search_for_failed_mix_of_constraints(
            FixedKeyAndMaskConstraint, tracked_set,
            utility_calls.locate_first_constraint_of_type(
                partition.constraints, FixedKeyAndMaskConstraint))
    if is_fixed_mask:
        valid = _search_for_failed_mix_of_constraints(
            FixedMaskConstraint, tracked_set,
            utility_calls.locate_first_constraint_of_type(
                partition.constraints, FixedMaskConstraint))
    if is_flexi_field:
        valid = _search_for_failed_mix_of_constraints(
            FlexiKeyFieldConstraint, tracked_set,
            utility_calls.locate_first_constraint_of_type(
                partition.constraints, FlexiKeyFieldConstraint))
    if is_fixed_field:
        valid = _search_for_failed_mix_of_constraints(
            FixedKeyFieldConstraint, tracked_set,
            utility_calls.locate_first_constraint_of_type(
                partition.constraints, FixedKeyFieldConstraint))
    if is_share_key:
        valid = True
    if is_continious:
        valid = _search_for_failed_mix_of_constraints(
            ContiguousKeyRangeContraint, tracked_set,
            utility_calls.locate_first_constraint_of_type(
                partition.constraints, ContiguousKeyRangeContraint))
    if (not is_continious and not is_fixed_key and not is_fixed_mask
            and not is_flexi_field and not is_fixed_field
            and not is_share_key):
        valid = True
    if not valid:
        raise Exception(
            "The merger of {} into the set {} failed as constraint {} is not "
            "compatible with the set".format(
                partition, tracked_set, constraint))


def _search_for_failed_mix_of_constraints(
        constraint_type, set_of_partitions, constraint_to_test_against):
    for partition in set_of_partitions:
        for other_constraint in utility_calls.locate_constraints_of_type(
                partition.constraints, constraint_type):
            if constraint_to_test_against != other_constraint:
                return False
    return True


def _linked_shared_constraints(
        fixed_key_groups, fixed_mask_groups, fixed_field_groups,
        flexi_field_groups, continuous_groups, none_continuous_groups,
        is_fixed_mask, is_fixed_key, is_flexi_field,
        is_fixed_field, partition, shared_key_mappings, shared_key_groups,
        is_shared_key, is_continuous):

    new_set = OrderedSet()
    new_set.add(partition)

    group = _find_group(
        fixed_key_groups, fixed_mask_groups, fixed_field_groups,
        flexi_field_groups, continuous_groups, none_continuous_groups,
        shared_key_groups, is_fixed_mask, is_fixed_key, is_flexi_field,
        is_fixed_field, is_shared_key, is_continuous)

    shared_key_mappings[partition] = (new_set, group)
    group.append(new_set)
    return new_set, group

def _find_group(
        fixed_key_groups, fixed_mask_groups, fixed_field_groups,
        flexi_field_groups, continuous_groups, none_continuous_groups,
        shared_key_groups, is_fixed_mask, is_fixed_key, is_flexi_field,
        is_fixed_field, is_shared_key, is_continuous):
    if is_fixed_key:
        return fixed_key_groups
    elif is_fixed_mask:
        return fixed_mask_groups
    elif is_flexi_field:
        return flexi_field_groups
    elif is_fixed_field:
        return fixed_field_groups
    elif is_shared_key:
        return shared_key_groups
    elif is_continuous:
        return continuous_groups
    else:
        return none_continuous_groups


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

    return is_continuous, is_fixed_mask, is_fixed_key, is_flexi_field, \
        is_fixed_field, is_shared_key


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
