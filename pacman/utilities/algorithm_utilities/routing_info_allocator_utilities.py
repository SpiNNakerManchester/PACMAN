# pacman imports
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
from pacman.exceptions import (
    PacmanValueError, PacmanConfigurationException,
    PacmanInvalidParameterException, PacmanRouteInfoAllocationException)
from spinn_utilities.ordered_set import OrderedSet

import logging

logger = logging.getLogger(__name__)


class _LabeledList(list):
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
    fixed_key_groups = _LabeledList("fixed_key")
    shared_key_groups = _LabeledList("share_key")
    fixed_mask_groups = _LabeledList("fixed_mask")
    fixed_field_groups = _LabeledList("fixed_field")
    flexi_field_groups = _LabeledList("flexi_field")
    continuous_groups = _LabeledList("continious")
    none_continuous_groups = _LabeledList("none_continious")

    # mapping between partition, set of partitions sharing key, and
    # constraint group
    partition_mappings = dict()

    # process each partition one by one in a bubble sort kinda way
    for vertex in machine_graph.vertices:
        for partition in machine_graph.\
                get_outgoing_edge_partitions_starting_at_vertex(vertex):

            # only process partitions of the correct traffic type
            if partition.traffic_type == traffic_type:

                # process the partition into the correct fields
                _process_partition(
                    fixed_key_groups=fixed_key_groups,
                    shared_key_groups=shared_key_groups,
                    fixed_mask_groups=fixed_mask_groups,
                    fixed_field_groups=fixed_field_groups,
                    flexi_field_groups=flexi_field_groups,
                    continuous_groups=continuous_groups,
                    none_continuous_groups=none_continuous_groups,
                    partition=partition, partition_mappings=partition_mappings)

    # return the set of groups
    return (fixed_key_groups, shared_key_groups,
            fixed_mask_groups, fixed_field_groups, flexi_field_groups,
            continuous_groups, none_continuous_groups)


def _process_partition(
        fixed_key_groups, shared_key_groups, fixed_mask_groups,
        fixed_field_groups, flexi_field_groups, continuous_groups,
        none_continuous_groups, partition, partition_mappings):
    """ handles the discovery of this partitions key group based off previous\
    processed and its constraints
    
    :param fixed_key_groups: the group of sets of fixed key partitions, where \
    each set is a set of partitions which share the same key
    :param shared_key_groups: the group of sets of partitions with only share \
    key constraints, where each set is a set of partitions which share the\
     same key
    :param fixed_mask_groups: the group of sets of fixed masks partitions, \
    where each set is a set of partitions which share the same key
    :param fixed_field_groups:  the group of sets of fixed field partitions, \
    where each set is a set of partitions which share the same key
    :param flexi_field_groups: the group of sets of flexi field partitions, \
    where each set is a set of partitions which share the same key.
    :param continuous_groups: the group of sets of continuous key partitions, \
    where each set is a set of partitions which share the same key.
    :param none_continuous_groups: the group of sets of none continuous key \
    partitions, where each set is a set of partitions which share the same key. 
    :param partition: The partition to place in the correct group.
    :param partition_mappings: the mapping between partition and (set of \
    partitions which share the same key, constraint group) 
    :rtype: None 
    """

    # get types of constraints from this partition
    (is_continuous, is_fixed_mask, is_fixed_key, is_flexi_field,
     is_fixed_field, is_shared_key) = _check_types_of_constraints(
        partition.constraints)

    # this partition already in a share key somewhere, merge in
    if partition in partition_mappings:

        # locate previous referral
        tracked_set, group_currently_resides_in = partition_mappings[partition]

        # locate real group
        real_group = _find_group(
            fixed_key_groups=fixed_key_groups,
            fixed_mask_groups=fixed_mask_groups,
            fixed_field_groups=fixed_field_groups,
            flexi_field_groups=flexi_field_groups,
            continuous_groups=continuous_groups,
            none_continuous_groups=none_continuous_groups,
            is_fixed_mask=is_fixed_mask, is_fixed_key=is_fixed_key,
            is_flexi_field=is_flexi_field, is_fixed_field=is_fixed_field,
            shared_key_groups=shared_key_groups,
            is_shared_key=is_shared_key, is_continuous=is_continuous)

        # if not in the correct group, switch groups.
        if group_currently_resides_in != real_group:

            # create new tracked_set with this partition in front, as it
            #  governed the move
            new_tracked_set = OrderedSet()
            new_tracked_set.add(partition)
            for partition_to_move in tracked_set:
                new_tracked_set.add(partition_to_move)

            # remove mapping from wrong set, add to right set
            group_currently_resides_in.remove(tracked_set)

            # set tracked set to be new tracked set
            tracked_set = new_tracked_set
            real_group.append(tracked_set)

            # update partition mapping accordingly
            for partition in tracked_set:
                partition_mappings[partition] = (tracked_set, real_group)

            # verify the move is a valid move (no conflicting constraints)
            _verify_constraints(
                tracked_set=tracked_set, fixed_mask_groups=fixed_mask_groups,
                continious_key_groups=continuous_groups,
                fixed_field_groups=fixed_field_groups,
                fixed_key_groups=fixed_key_groups,
                group=group_currently_resides_in,
                flexi_field_groups=flexi_field_groups,
                share_key_groups=shared_key_groups)

        # if share key, locate and find partitions to merge
        if is_shared_key:
            # get share key constraint that must be there
            other_partitions = \
                utility_calls.locate_first_constraint_of_type(
                    partition.constraints, ShareKeyConstraint).other_partitions

            # search for merging groups
            tracked_set, real_group = _search_for_merger(
                other_partitions, partition_mappings, tracked_set,
                group_currently_resides_in, fixed_key_groups,
                fixed_mask_groups, fixed_field_groups, flexi_field_groups,
                continuous_groups, shared_key_groups)

            # verify constraints are correct
            _verify_constraints(
                is_fixed_mask, is_fixed_key, is_flexi_field,
                is_fixed_field, is_shared_key, is_continuous, tracked_set,
                real_group)

    else:  # not in a group already. store itself and then search
        tracked_set, real_group = _linked_shared_constraints(
            fixed_key_groups, fixed_mask_groups, fixed_field_groups,
            flexi_field_groups, continuous_groups,
            none_continuous_groups, is_fixed_mask, is_fixed_key,
            is_flexi_field, is_fixed_field, partition, partition_mappings,
            shared_key_groups, is_shared_key, is_continuous)

        if is_shared_key:  # if is share key, look for any already in existence

            # get share key
            other_partitions = \
                utility_calls.locate_first_constraint_of_type(
                    partition.constraints, ShareKeyConstraint).other_partitions

            # search for merger
            tracked_set, real_group = _search_for_merger(
                other_partitions, partition_mappings, tracked_set, real_group,
                fixed_key_groups, fixed_mask_groups, fixed_field_groups,
                flexi_field_groups, continuous_groups, shared_key_groups)

            # verify the constraints of the tracked set
            _verify_constraints(
                fixed_mask_groups, fixed_key_groups, flexi_field_groups,
                fixed_field_groups, shared_key_groups, continuous_groups,
                tracked_set, real_group)


def _locate_chief_group(
        group_1, group_1_list, group_2, group_2_list, share_key_group):
    """ from 2 groups, decides which one should be merged into which, based
    off the heuristic that share key group is to 
    
    :param group_1: 
    :param group_1_list: 
    :param group_2: 
    :param group_2_list: 
    :param share_key_group: 
    :return: 
    """
    # hand over the none share key group if one exists
    if group_1 == share_key_group and group_2 != share_key_group:
        return group_2, group_2_list, group_1, group_1_list
    elif group_1 != share_key_group and group_2 == share_key_group:
        return group_1, group_1_list, group_2, group_2_list
    # if both share key, just had the first one, doesnt matter which
    elif group_1 == share_key_group and group_2 == share_key_group:
        return group_1, group_1_list, group_2, group_2_list
    # if same group and not share key, just hand first, doesnt matter
    elif (group_1 != share_key_group and group_2 != share_key_group and
            (id(group_1) == id(group_2))):
        return group_1, group_1_list, group_2, group_2_list
    else:  # if not share key, and both are different, theres a mismatch of
        # constraints. blow up.
        raise Exception(
            "cannot deduce which group to merge key constraints into. Please "
            "fix and try again")


def _search_for_merger(
        other_partitions, partition_mappings, mergable_list,
        mergable_group, fixed_key_groups, fixed_mask_groups,
        fixed_field_groups, flexi_field_groups, continuous_groups,
        shared_key_groups):

    # locate merge-able track list partition
    for other_partition in other_partitions:
        # check that no merger
        if other_partition in partition_mappings:

            # get other mapped version
            other_track_list, other_group = \
                partition_mappings[other_partition]

            # if different merge one into the other, if same, no point
            if mergable_list != other_track_list:

                # find which one to merge into which
                mergable_group, mergable_list, minion_group, minion_list = \
                    _locate_chief_group(
                        mergable_group, mergable_list, other_group,
                        other_track_list, shared_key_groups)

                # update the list with one that needs merging
                mergable_list.update(minion_list)

                # remove mapping for other set, as now its in my set
                minion_group.remove(minion_list)

                # update partition to set mapping
                for minion_partition in minion_list:
                    partition_mappings[minion_partition] = \
                        (mergable_list, mergable_group)

                # check all constraints match again
                _verify_constraints(
                    fixed_mask_groups, fixed_key_groups,
                    flexi_field_groups, fixed_field_groups, shared_key_groups,
                    continuous_groups, mergable_list, mergable_group)
        else:  # not seen before, just add to the mergable list
            mergable_list.add(other_partition)
            partition_mappings[other_partition] = (
                mergable_list, mergable_group)

    # return the final list and group
    return mergable_list, mergable_group


def _locate_constraint_type(
        group, fixed_mask_groups, fixed_key_groups, flexi_field_groups,
        fixed_field_groups, share_key_groups, continious_key_groups):
    if id(group) == id(fixed_key_groups):
        return FixedKeyAndMaskConstraint
    if id(group) == id(fixed_mask_groups):
        return FixedMaskConstraint
    if id(group) == id(flexi_field_groups):
        return FlexiKeyFieldConstraint
    if id(group) == id(fixed_field_groups):
        return FixedKeyFieldConstraint
    if id(group) == id(share_key_groups):
        return ShareKeyConstraint
    if id(group) == id(continious_key_groups):
        return ContiguousKeyRangeContraint
    else:
        return None


def _verify_constraints(
        fixed_mask_groups, fixed_key_groups, flexi_field_groups,
        fixed_field_groups, share_key_groups, continious_key_groups,
        tracked_set, group):

    constraint_type = _locate_constraint_type(
        group, fixed_mask_groups, fixed_key_groups, flexi_field_groups,
        fixed_field_groups, share_key_groups, continious_key_groups)

    # if theres any constraints to check for, check
    if constraint_type is not None:

        # merge all constraints
        constraints = list()
        for partition in tracked_set:
            constraints.extend(partition.constraints)

        # if not share key, find any conflicting constraints
        if constraint_type != ShareKeyConstraint:
            valid = _search_for_failed_mix_of_constraints(
                constraint_type, constraints,
                utility_calls.locate_first_constraint_of_type(
                    constraints, constraint_type))
            if not valid:
                raise PacmanRouteInfoAllocationException(
                    "The merged set of {} failed as their constraints {} are "
                    " not compatible with the sets group of {}".format(
                        tracked_set, constraints, constraint_type))


def _search_for_failed_mix_of_constraints(
        constraint_type, constraints, constraint_to_test_against):
    all_constraints = [FixedKeyFieldConstraint, FlexiKeyFieldConstraint,
                       FixedMaskConstraint, FixedKeyAndMaskConstraint]
    all_constraints.remove(constraint_type)
    for other_constraint in utility_calls.locate_constraints_of_type(
            constraints, constraint_type):
        if constraint_to_test_against != other_constraint:
            return False
    for fail_constraint_type in all_constraints:
        if len(utility_calls.locate_constraints_of_type(
                constraints, fail_constraint_type)) > 0:
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
    """ given the flags, finds the group it should reside in
    
    :param fixed_key_groups: 
    :param fixed_mask_groups: 
    :param fixed_field_groups: 
    :param flexi_field_groups: 
    :param continuous_groups: 
    :param none_continuous_groups: 
    :param shared_key_groups: 
    :param is_fixed_mask: 
    :param is_fixed_key: 
    :param is_flexi_field: 
    :param is_fixed_field: 
    :param is_shared_key: 
    :param is_continuous: 
    :return: 
    """
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
    """ helper method for the partition grouping. Iterates though the \
    constraints and determines what functionality it represents in the end.
    
    :param constraints: the list of constraints to check
    :return: 6 booleans each of which covers if a specific functional\
     constraint exists in the set
     :rtype: 6 bools (1. if there's a continuous key constraint.\
                      2. if there's a fixed mask constraint.\
                      3. if there's a fixed key constraint.\
                      4. if there's a flexi field constraint.\
                      5. if there's a fixed field constraint.\
                      6. if there's a share key constraint.
    """

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
