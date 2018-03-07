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
    share_key_constraint import ShareKeyConstraint
from pacman.utilities.utility_calls import locate_constraints_of_type
from pacman.exceptions import (
    PacmanValueError, PacmanConfigurationException,
    PacmanInvalidParameterException, PacmanRouteInfoAllocationException)

import logging
from six import itervalues

logger = logging.getLogger(__name__)


class ConstraintGroup(list):

    def __init__(self, values):
        super(ConstraintGroup, self).__init__(values)
        self._constraint = None
        self._n_keys = None

    @property
    def constraint(self):
        return self._constraint

    def _set_constraint(self, constraint):
        self._constraint = constraint

    def __hash__(self):
        return id(self).__hash__()

    def __eq__(self, other):
        return id(other) == id(self)


def get_edge_groups(machine_graph, traffic_type):
    """ Utility method to get groups of edges using any\
        :py:class:`pacman.model.constraints.key_allocator_constraints.KeyAllocatorSameKeyConstraint`\
        constraints.  Note that no checking is done here about conflicts\
        related to other constraints.

    :param machine_graph: the machine graph
    :param traffic_type: the traffic type to group
    """

    # mapping between partition and shared key group it is in
    partition_groups = dict()

    # process each partition one by one in a bubble sort kinda way
    for vertex in machine_graph.vertices:
        for partition in machine_graph.\
                get_outgoing_edge_partitions_starting_at_vertex(vertex):

            # only process partitions of the correct traffic type
            if partition.traffic_type == traffic_type:

                # Get a set of partitions that should be grouped together
                shared_key_constraints = locate_constraints_of_type(
                    partition.constraints, ShareKeyConstraint)
                partitions_to_group = [partition]
                for constraint in shared_key_constraints:
                    partitions_to_group.extend(constraint.other_partitions)

                # Get a set of groups that should be grouped
                groups_to_group = [
                    partition_groups.get(part_to_group, [part_to_group])
                    for part_to_group in partitions_to_group]

                # Group the groups
                new_group = ConstraintGroup(
                    part for group in groups_to_group for part in group)
                partition_groups.update(
                    {part: new_group for part in new_group})

    # Keep track of groups
    fixed_key_groups = list()
    shared_key_groups = list()
    fixed_mask_groups = list()
    fixed_field_groups = list()
    flexi_field_groups = list()
    continuous_groups = list()
    noncontinuous_groups = list()
    groups_by_type = {
        FixedKeyAndMaskConstraint: fixed_key_groups,
        FixedMaskConstraint: fixed_mask_groups,
        FixedKeyFieldConstraint: fixed_field_groups,
        FlexiKeyFieldConstraint: flexi_field_groups,
    }
    groups = set(itervalues(partition_groups))
    for group in groups:

        # Get all expected constraints in the group
        constraints = [
            constraint for partition in group
            for constraint in locate_constraints_of_type(
                partition.constraints,
                (FixedKeyAndMaskConstraint, FixedMaskConstraint,
                 FlexiKeyFieldConstraint, FixedKeyFieldConstraint))]

        # Check that the possibly conflicting constraints are equal
        if constraints and not all(
                constraint_a == constraint_b for constraint_a in constraints
                for constraint_b in constraints):
            raise PacmanRouteInfoAllocationException(
                "The group of partitions {} have conflicting constraints"
                .format(constraints))

        # If no constraints, must be one of the non-specific groups
        if not constraints:
            # If the group has only one item, it is not shared
            if len(group) == 1:
                continuous_constraints = [
                    constraint for partition in group
                    for constraint in locate_constraints_of_type(
                        constraints, ContiguousKeyRangeContraint)]
                if continuous_constraints:
                    continuous_groups.append(group)
                else:
                    noncontinuous_groups.append(group)

            # If the group has more than one partition, it must be shared
            else:
                shared_key_groups.append(group)

        # If constraints found, put the group in the appropriate constraint
        # group
        else:
            group._set_constraint(constraints[0])
            constraint_type = type(constraints[0])
            groups_by_type[constraint_type].append(group)

    # return the set of groups
    return (fixed_key_groups, shared_key_groups,
            fixed_mask_groups, fixed_field_groups, flexi_field_groups,
            continuous_groups, noncontinuous_groups)


def check_types_of_edge_constraint(machine_graph):
    """ Go through the graph for operations and checks that the constraints\
        are compatible.

    :param machine_graph: the graph to search through
    :rtype: None:
    """
    for partition in machine_graph.outgoing_edge_partitions:
        fixed_key = locate_constraints_of_type(
            partition.constraints, FixedKeyAndMaskConstraint)

        fixed_mask = locate_constraints_of_type(
            partition.constraints, FixedMaskConstraint)

        fixed_field = locate_constraints_of_type(
            partition.constraints, FixedKeyFieldConstraint)

        flexi_field = locate_constraints_of_type(
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

    :param partition: \
        the outgoing_edge_partition to search for these constraints
    :rtype: None:
    """
    fixed_mask = locate_constraints_of_type(
        partition.constraints, FixedMaskConstraint)[0]
    fixed_field = locate_constraints_of_type(
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
            if other_field != field and other_field.mask & field.mask != 0:
                raise PacmanInvalidParameterException(
                    "field.mask, mask",
                    "Field masks {} and {} overlap".format(
                        field.mask, other_field.mask),
                    "{}:{}".format(field.mask, mask))


def get_fixed_mask(same_key_group):
    """ Get a fixed mask from a group of edges if a\
        :py:class:`pacman.model.constraints.key_allocator_constraints.FixedMaskConstraint`\
        constraint exists in any of the edges in the group.

    :param same_key_group: \
        Set of edges that are to be assigned the same keys and masks
    :type same_key_group: iterable of\
        :py:class:`pacman.model.graphs.machine.MachineEdge`
    :return: The fixed mask if found, or None
    :raise PacmanValueError: If two edges conflict in their requirements
    """
    mask = None
    fields = None
    edge_with_mask = None
    for edge in same_key_group:
        fixed_mask_constraints = locate_constraints_of_type(
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
