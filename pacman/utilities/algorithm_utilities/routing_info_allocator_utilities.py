# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import OrderedDict
import logging
import numpy
from six import itervalues
from six.moves import xrange
from spinn_utilities.ordered_set import OrderedSet
from pacman.model.constraints.key_allocator_constraints import (
    FixedKeyFieldConstraint,
    ContiguousKeyRangeContraint, FixedMaskConstraint,
    FixedKeyAndMaskConstraint, ShareKeyConstraint)
from pacman.utilities.utility_calls import (
    locate_constraints_of_type, expand_to_bit_array, compress_from_bit_array)
from pacman.exceptions import (
    PacmanValueError, PacmanConfigurationException,
    PacmanInvalidParameterException, PacmanRouteInfoAllocationException)

logger = logging.getLogger(__name__)


class ConstraintGroup(list):
    """ A list of edges that share a constraint.
    """

    def __init__(self, values):
        """
        :param iterable(OutgoingEdgePartition) values:
        """
        super(ConstraintGroup, self).__init__(values)
        self._constraint = None
        self._n_keys = None

    @property
    def constraint(self):
        """ The shared constraint.

        :rtype: AbstractConstraint
        """
        return self._constraint

    def _set_constraint(self, constraint):
        self._constraint = constraint

    def __hash__(self):
        return id(self).__hash__()

    def __eq__(self, other):
        return id(other) == id(self)

    def __ne__(self, other):
        return id(other) != id(self)


_ALL_FIXED_TYPES = (
    FixedKeyAndMaskConstraint, FixedMaskConstraint, FixedKeyFieldConstraint)


def get_edge_groups(machine_graph, traffic_type):
    """ Utility method to get groups of edges using any\
        :py:class:`KeyAllocatorSameKeyConstraint` constraints.  Note that no\
        checking is done here about conflicts related to other constraints.

    :param MachineGraph machine_graph: the machine graph
    :param EdgeTrafficType traffic_type: the traffic type to group
    :return: (fixed key groups, shared key groups, fixed mask groups,
        fixed field groups, continuous groups, noncontinuous groups)
    :rtype: tuple(list(ConstraintGroup), list(ConstraintGroup),
        list(ConstraintGroup), list(ConstraintGroup), list(ConstraintGroup),
        list(ConstraintGroup))
    """

    # mapping between partition and shared key group it is in
    partition_groups = OrderedDict()

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
    continuous_groups = list()
    noncontinuous_groups = list()
    groups_by_type = {
        FixedKeyAndMaskConstraint: fixed_key_groups,
        FixedMaskConstraint: fixed_mask_groups,
        FixedKeyFieldConstraint: fixed_field_groups,
    }
    groups = OrderedSet(itervalues(partition_groups))
    for group in groups:

        # Get all expected constraints in the group
        constraints = [
            constraint for partition in group
            for constraint in locate_constraints_of_type(
                partition.constraints, _ALL_FIXED_TYPES)]

        # Check that the possibly conflicting constraints are equal
        if constraints and not all(
                constraint_a == constraint_b for constraint_a in constraints
                for constraint_b in constraints):
            raise PacmanRouteInfoAllocationException(
                "The group of partitions {} have conflicting constraints"
                .format(constraints))

        # If constraints found, put the group in the appropriate constraint
        # group
        if constraints:
            group._set_constraint(constraints[0])
            constraint_type = type(constraints[0])
            groups_by_type[constraint_type].append(group)
        # If no constraints, must be one of the non-specific groups
        # If the group has only one item, it is not shared
        elif len(group) == 1:
            continuous_constraints = (
                constraint for partition in group
                for constraint in locate_constraints_of_type(
                    constraints, ContiguousKeyRangeContraint))
            if any(continuous_constraints):
                continuous_groups.append(group)
            else:
                noncontinuous_groups.append(group)
        # If the group has more than one partition, it must be shared
        else:
            shared_key_groups.append(group)

    # return the set of groups
    return (fixed_key_groups, shared_key_groups, fixed_mask_groups,
            fixed_field_groups, continuous_groups, noncontinuous_groups)


def check_types_of_edge_constraint(machine_graph):
    """ Go through the graph for operations and checks that the constraints\
        are compatible.

    :param MachineGraph machine_graph: the graph to search through
    :raises PacmanConfigurationException: if a problem is found
    """
    for partition in machine_graph.outgoing_edge_partitions:
        fixed_key = locate_constraints_of_type(
            partition.constraints, FixedKeyAndMaskConstraint)
        fixed_mask = locate_constraints_of_type(
            partition.constraints, FixedMaskConstraint)
        fixed_field = locate_constraints_of_type(
            partition.constraints, FixedKeyFieldConstraint)

        if len(fixed_key) > 1 or len(fixed_field) > 1 or len(fixed_mask) > 1:
            raise PacmanConfigurationException(
                "There are multiple constraint of the same type on partition "
                "{} starting at {}. Please fix and try again.".format(
                    partition.identifier, partition.pre_vertex))

        fixed_key = len(fixed_key) == 1
        fixed_mask = len(fixed_mask) == 1
        fixed_field = len(fixed_field) == 1

        # check for fixed key and a fixed mask. as these should have been
        # merged before now
        if fixed_key and fixed_mask:
            raise PacmanConfigurationException(
                "The partition {} starting at {} has a fixed key and fixed "
                "mask constraint. These can be merged together, but is "
                "deemed an error here".format(
                    partition.identifer, partition.pre_vertex))

        # check for a fixed key and fixed field, as these are incompatible
        if fixed_key and fixed_field:
            raise PacmanConfigurationException(
                "The partition {} starting at {} has a fixed key and fixed "
                "field constraint. These may be merge-able together, but is "
                "deemed an error here".format(
                    partition.identifer, partition.pre_vertex))

        # check that a fixed mask and fixed field have compatible masks
        if fixed_mask and fixed_field:
            _check_masks_are_correct(partition)


def _check_masks_are_correct(partition):
    """ Check that the masks between a fixed mask constraint and a fixed_field\
        constraint. Raises error if not.

    :param OutgoingEdgePartition partition:
        the outgoing_edge_partition to search for these constraints
    :raise PacmanInvalidParameterException: if the masks are incompatible
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
        :py:class:`FixedMaskConstraint`\
        constraint exists in any of the edges in the group.

    :param iterable(MachineEdge) same_key_group:
        Set of edges that are to be assigned the same keys and masks
    :return: The fixed mask if found, or None
    :rtype: tuple(int or None, iterable(Field) or None)
    :raise PacmanValueError: If two edges conflict in their requirements
    """
    mask = None
    fields = None
    edge_with_mask = None
    for edge in same_key_group:
        for constraint in locate_constraints_of_type(
                edge.constraints, FixedMaskConstraint):
            if mask is not None and mask != constraint.mask:
                raise PacmanValueError(
                    "Two Edges {} and {} must have the same key and mask, "
                    "but have different fixed masks, {} and {}".format(
                        edge, edge_with_mask, mask, constraint.mask))
            if (fields is not None and constraint.fields is not None and
                    fields != constraint.fields):
                raise PacmanValueError(
                    "Two Edges {} and {} must have the same key and mask, "
                    "but have different field ranges".format(
                        edge, edge_with_mask))
            mask = constraint.mask
            edge_with_mask = edge
            if constraint.fields is not None:
                fields = constraint.fields

    return mask, fields


def generate_key_ranges_from_mask(key, mask):
    """ Get a generator of base_key, n_keys pairs that represent ranges\
        allowed by the mask

    :param key: The base key
    :param mask: The mask
    :return: generator of two ints representing the key field, and the n keys\
        for that field
    :rtype: iterator(tuple(int, int))
    """
    unwrapped_mask = expand_to_bit_array(mask)
    first_zeros = list()
    remaining_zeros = list()
    pos = len(unwrapped_mask) - 1

    # Keep the indices of the first set of zeros
    while pos >= 0 and unwrapped_mask[pos] == 0:
        first_zeros.append(pos)
        pos -= 1

    # Find all the remaining zeros
    while pos >= 0:
        if unwrapped_mask[pos] == 0:
            remaining_zeros.append(pos)
        pos -= 1

    # Loop over 2^len(remaining_zeros) to produce the base key,
    # with n_keys being 2^len(first_zeros)
    n_sets = 2 ** len(remaining_zeros)
    n_keys = 2 ** len(first_zeros)
    if not remaining_zeros:
        yield key, n_keys
        return
    unwrapped_key = expand_to_bit_array(key)
    for value in xrange(n_sets):
        generated_key = numpy.copy(unwrapped_key)
        unwrapped_value = expand_to_bit_array(value)[
            -len(remaining_zeros):]
        generated_key[remaining_zeros] = unwrapped_value
        yield compress_from_bit_array(generated_key), n_keys
