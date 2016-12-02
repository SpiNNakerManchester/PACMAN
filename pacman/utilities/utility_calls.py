from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanValueError

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
    passed_constraints = list()
    for constraint in constraints:
        if isinstance(constraint, constraint_type):
            passed_constraints.append(constraint)
    return passed_constraints


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
                        "Constraints of this class are not supported by this"
                        " algorithm")


def check_constrained_value(value, current_value):
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


def is_equal_or_None(a, b):
        """ If a and b are both not None, return True iff they are equal,\
            otherwise return True
        """
        return True if a is None or b is None or a == b else False
