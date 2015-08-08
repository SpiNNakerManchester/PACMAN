from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanConfigurationException
from pacman.exceptions import PacmanValueError

from pacman.model.constraints.abstract_constraints.\
    abstract_placer_constraint \
    import AbstractPlacerConstraint
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_iptag_constraint \
    import TagAllocatorRequireIptagConstraint
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_reverse_iptag_constraint \
    import TagAllocatorRequireReverseIptagConstraint

import numpy


def locate_constraints_of_type(constraints, constraint_type):
    """ Locates all constraints of a given type out of a list

    :param constraints: The constraints to filter
    :type constraints: iterable of\
                :py:class:`pacman.model.constraints.AbstractConstraint.AbstractConstraint`
    :param constraint_type: The type of constraints to return
    :type constraint_type:\
                :py:class:`pacman.model.constraint.abstract_partitioner_constraint.AbstractPartitionConstraint`
    :return: The constraints of constraint_type that are\
                found in the constraints given
    :rtype: iterable of\
                :py:class:`pacman.model.constraints.AbstractConstraint.AbstractConstraint`
    :raises None: no known exceptions
    """
    # ADR replaced "long-form" loop with comprehension (marginally improved
    # efficiency for no degradation in readability)
    return [constraint for constraint in constraints
            if isinstance(constraint, constraint_type)]

def check_algorithm_can_support_constraints(
        constrained_vertices, supported_constraints, abstract_constraint_type):
    """ Helper method to find out if an algorithm can support all the\
        constraints given the objects its expected to work on

    :param constrained_vertices: a list of constrained vertices which each has\
                constraints given to the algorithm
    :type constrained_vertices: iterable of\
                :py:class:`pacman.model.constraints.AbstractConstraint.AbstractConstraint`
    :param supported_constraints: The constraints supported
    :type supported_constraints: iterable of\
                :py:class:`pacman.model.constraints.AbstractConstraint.AbstractConstraint`
    :param abstract_constraint_type: The overall abstract constraint type\
                supported
    :type abstract_constraint_type:\
                :py:class:`pacman.model.constraints.AbstractConstraint.AbstractConstraint`
    :return: Nothing is returned
    :rtype: None
    :raise pacman.exceptions.PacmanInvalidParameterException: when the\
                algorithm cannot support the constraints demanded of it
    """
    for constrained_vertex in constrained_vertices:
        for constraint in constrained_vertex.constraints:
            if isinstance(constraint, abstract_constraint_type):
                found = False
                for supported_constraint in supported_constraints:
                    if isinstance(constraint, supported_constraint):
                        found = True
                        break

                if not found:
                    raise PacmanInvalidParameterException(
                        "constraints", constraint.__class__,
                        "Vertex %s has constraint %s not supported by this"
                        " algorithm" % (constrained_vertex.label, 
                                    constraint.__class__.__name__))
                    return False
    return True


def sort_objects_by_constraint_authority(objects):
    """ Takes the subverts of a subgraph and orders them into a list\
        with a order based off rank on the constraint\
    :param objects: The objects to be sorted. need to have a constraints
    :type objects: iterable of soem object with constraints
    :return: A list of ordered objects
    :rtype: list of objects
    :raise None: this method does not raise any known exceptions
    """
    objects_with_rank = list()
    for current_object in objects:
        if not hasattr(current_object, "constraints"):
            raise PacmanConfigurationException(
                "the object given to the "
                "sort_objects_by_constraint_authority method does not "
                "contain constraints. Every object must have at least a "
                "max atoms per core constraint")
        max_rank_so_far = 0
        for constraint in current_object.constraints:
            # only store ranks for placer contraints and ones that are better
            # than already seen
            if (isinstance(constraint, AbstractPlacerConstraint) and
                    constraint.get_rank() >= max_rank_so_far):
                max_rank_so_far = constraint.get_rank()
        objects_with_rank.append((current_object, max_rank_so_far))

    ordered_objects = sorted(objects_with_rank,
                             key=lambda cur_item: cur_item[1],
                             reverse=True)
    return [item[0] for item in ordered_objects]


def _check_constrained_value(value, current_value):
    """ Checks that the current value and a new value match

    :param value: The value to check
    :param current_value: The existing value
    """
    if (current_value is not None and value is not None and
            value != current_value):
        raise PacmanValueError(
            "Multiple constraints with conflicting values")
    if value is not None:
        return value
    return current_value


def get_chip_and_core(constraints, chips=None):
    """ Get an assigned chip and core from a set of constraints

    :param constraints: The set of constraints to get the values from.  Note\
                that any type of constraint can be in the list but only those\
                relevant will be used
    :type constraints: iterable of\
                :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
    :param chips: Optional list of tuples of (x, y) coordinates of chips,\
                restricting the allowed chips
    :type chips: iterable of (int, int)
    :return: tuple of a chip x and y coordinates, and processor id, any of\
                which might be None
    :rtype: (tuple of (int, int, int)
    """
    x = None
    y = None
    p = None
    for constraint in constraints:
        if isinstance(constraint, PlacerChipAndCoreConstraint):
            x = _check_constrained_value(constraint.x, x)
            y = _check_constrained_value(constraint.y, y)
            p = _check_constrained_value(constraint.p, p)

    if chips is not None and x is not None and y is not None:
        if (x, y) not in chips:
            raise PacmanInvalidParameterException(
                "x, y and chips",
                "{}, {} and {}".format(x, y, chips),
                "The constraint cannot be met with the given chips")
    return x, y, p


def get_ip_tag_info(constraints):
    """ Get the ip tag constraint information from the constraints

    :param constraints: The set of constraints to get the values from.  Note\
                that any type of constraint can be in the list but only those\
                relevant will be used
    :type constraints: iterable of\
                :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
    :return: A tuple of board address, iterable of ip tag constraints and \
                iterable of reverse ip tag constraints
    :rtype: (str, iterable of\
                :py:class:`pacman.model.constraints.tag_allocator_constraints.tag_allocator_require_iptag_constraint.TagAllocatorRequireIptagConstraint`,
                iterable of\
                :py:class:`pacman.model.constraints.tag_allocator_constraints.tag_allocator_require_reverse_iptag_constraint.TagAllocatorRequireReverseIptagConstraint`)
    """
    board_address = None
    ip_tags = list()
    reverse_ip_tags = list()
    for constraint in constraints:
        if isinstance(constraint,
                      TagAllocatorRequireIptagConstraint):
            board_address = _check_constrained_value(
                constraint.board_address, board_address)
            ip_tags.append(constraint)
        if isinstance(constraint,
                      TagAllocatorRequireReverseIptagConstraint):
            board_address = _check_constrained_value(
                constraint.board_address, board_address)
            reverse_ip_tags.append(constraint)
    return board_address, ip_tags, reverse_ip_tags


def expand_to_bit_array(value):
    """ Expand a 32-bit value in to an array of length 32 of uint8 values,\
        each of which is a 1 or 0

    :param value: The value to expand
    :type value: int
    :rtype: [uint8]
    """
    return numpy.unpackbits(
        numpy.asarray([value], dtype=">u4").view(dtype="uint8"))


def compress_from_bit_array(bit_array):
    """ Compress a bit array of 32 uint8 values, where each is a 1 or 0,\
        into a 32-bit value

    :param bit_array: The array to compress
    :type bit_array: [uint8]
    :rtype: int
    """
    return numpy.packbits(bit_array).view(dtype=">u4")[0].item()


def compress_bits_from_bit_array(bit_array, bit_positions):
    """ Compress specific positions from a bit array of 32 uint8 value,\
        where is a 1 or 0, into a 32-bit value.

    :param bit_array: The array to extract the value from
    :type bit_array: [uint8]
    :param bit_positions: The positions of the bits to extract, each value\
                being between 0 and 31
    :type bit_positions: [int]
    :rtype: int
    """
    expanded_value = numpy.zeros(32, dtype="uint8")
    expanded_value[-len(bit_positions):] = bit_array[bit_positions]
    return compress_from_bit_array(expanded_value)
