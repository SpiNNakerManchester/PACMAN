
# pacman imports
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_field_constraint import \
    KeyAllocatorFixedFieldConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_flexi_field_constraint import \
    KeyAllocatorFlexiFieldConstraint
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

import logging
logger = logging.getLogger(__name__)


def get_edge_groups(machine_graph):
    """ Utility method to get groups of edges using any\
        :py:class:`pacman.model.constraints.key_allocator_same_key_constraint.KeyAllocatorSameKeyConstraint`\
        constraints.  Note that no checking is done here about conflicts\
        related to other constraints.
    :param machine_graph: the machine graph
    """

    # Keep a dictionary of the group which contains an edge
    fixed_key_groups = set()
    fixed_mask_groups = set()
    fixed_field_groups = set()
    flexi_field_groups = set()
    continuous_groups = set()
    none_continuous_groups = list()
    for vertex in machine_graph.vertices:
        outgoing_edge_partitions = \
            machine_graph.get_outgoing_edge_partitions_starting_at_vertex(
                vertex)
        for partition in outgoing_edge_partitions:

            # assume all edges have the same constraints in them. use first one
            # to deduce which group to place it into
            constraints = partition.constraints
            is_continuous = False
            for constraint in constraints:
                if isinstance(constraint, KeyAllocatorFixedMaskConstraint):
                    fixed_mask_groups.add(partition)
                elif isinstance(constraint,
                                KeyAllocatorFixedKeyAndMaskConstraint):
                    fixed_key_groups.add(partition)
                elif isinstance(constraint, KeyAllocatorFlexiFieldConstraint):
                    flexi_field_groups.add(partition)
                elif isinstance(constraint, KeyAllocatorFixedFieldConstraint):
                    fixed_field_groups.add(partition)
                elif isinstance(constraint,
                                KeyAllocatorContiguousRangeContraint):
                    is_continuous = True
                    continuous_groups.add(partition)
            if not is_continuous:
                none_continuous_groups.append(partition)
    return (fixed_key_groups, fixed_mask_groups, fixed_field_groups,
            flexi_field_groups, continuous_groups, none_continuous_groups)


def check_types_of_edge_constraint(machine_graph):
    """ Go through the graph for operations and checks that the constraints\
        are compatible.

    :param machine_graph: the graph to search through
    :return:
    """
    for partition in machine_graph.outgoing_edge_partitions:
        fixed_key = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedKeyAndMaskConstraint)

        fixed_mask = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedMaskConstraint)

        fixed_field = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedFieldConstraint)

        flexi_field = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFlexiFieldConstraint)

        if (len(fixed_key) > 1 or len(fixed_field) > 1 or
                len(fixed_mask) > 1 or len(flexi_field) > 1):
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
                "field constraint. These may be merge-able together, but "
                "is deemed an error here"
                .format(partition.identifer, partition.edges))

        # check that a fixed mask and fixed field have compatible masks
        if fixed_mask and fixed_field:
            _check_masks_are_correct(partition)

        # check that if there's a flexible field, and something else, throw
        # error
        if flexi_field and (fixed_mask or fixed_key or fixed_field):
            raise exceptions.PacmanConfigurationException(
                "The partition {} for edges {} has a flexible field and "
                "another fixed constraint. These maybe be merge-able, but "
                "is deemed an error here"
                .format(partition.identifer, partition.edges))


def _check_masks_are_correct(partition):
    """ Check that the masks between a fixed mask constraint\
        and a fixed_field constraint. completes if its correct, raises error\
        otherwise

    :param partition: the outgoing_edge_partition to search for these\
                constraints
    :return:
    """
    fixed_mask = utility_calls.locate_constraints_of_type(
        partition.constraints, KeyAllocatorFixedMaskConstraint)[0]
    fixed_field = utility_calls.locate_constraints_of_type(
        partition.constraints, KeyAllocatorFixedFieldConstraint)[0]
    mask = fixed_mask.mask
    for field in fixed_field.fields:
        if field.mask & mask != field.mask:
            raise exceptions.PacmanInvalidParameterException(
                "field.mask, mask",
                "The field mask {} is outside of the mask {}".format(
                    field.mask, mask),
                "{}:{}".format(field.mask, mask))
        for other_field in fixed_field.fields:
            if (other_field != field and
                    other_field.mask & field.mask != 0):
                raise exceptions.PacmanInvalidParameterException(
                    "field.mask, mask",
                    "Field masks {} and {} overlap".format(
                        field.mask, other_field.mask),
                    "{}:{}".format(field.mask, mask))


def get_fixed_mask(same_key_group):
    """ Get a fixed mask from a group of edges if a\
        :py:class:`pacman.model.constraints.key_allocator_same_key_constraint.KeyAllocatorFixedMaskConstraint`\
        constraint exists in any of the edges in the group.

    :param same_key_group: Set of edges that are to be\
                assigned the same keys and masks
    :type same_key_group: iterable of\
                :py:class:`pacman.model.graph.machine.abstract_machine_edge.AbstractMachineEdge`
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
