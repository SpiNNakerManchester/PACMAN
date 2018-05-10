import hashlib
import numpy
from pacman.exceptions import (
    PacmanInvalidParameterException, PacmanValueError)


def locate_constraints_of_type(constraints, constraint_type):
    """ Locates all constraints of a given type out of a list

    :param constraints: The constraints to filter
    :type constraints: iterable of\
        :py:class:`pacman.model.constraints.AbstractConstraint`
    :param constraint_type: The type of constraints to return
    :type constraint_type:\
        :py:class:`pacman.model.constraints.partitioner_constraints.AbstractPartitionConstraint`
    :return: The constraints of constraint_type that are found in the \
        constraints given
    :rtype: iterable(\
        :py:class:`pacman.model.constraints.AbstractConstraint`)
    :raises None: no known exceptions
    """
    return [c for c in constraints if isinstance(c, constraint_type)]


def locate_first_constraint_of_type(constraints, constraint_type):
    """ Locates the first constraint of a given type out of a list

    :param constraints: The constraints to select from
    :type constraints: iterable(\
        :py:class:`pacman.model.constraints.AbstractConstraint`)
    :param constraint_type: The type of constraints to return
    :type constraint_type:\
        :py:class:`pacman.model.constraints.partitioner_constraints.AbstractPartitionConstraint`
    :return: The first constraint of constraint_type that was found in the\
        constraints given
    :rtype:\
        :py:class:`pacman.model.constraints.AbstractConstraint`
    :raises pacman.exceptions.PacmanInvalidParameterException: \
        If no such constraint is present
    """
    for constraint in constraints:
        if isinstance(constraint, constraint_type):
            return constraint
    raise PacmanInvalidParameterException(
        "constraints", constraint_type.__class__,
        "Constraints of this class are not present")


def _is_constraint_supported(constraint, supported_constraints):
    return any(isinstance(constraint, supported_constraint)
               for supported_constraint in supported_constraints)


def check_algorithm_can_support_constraints(
        constrained_vertices, supported_constraints, abstract_constraint_type):
    """ Helper method to find out if an algorithm can support all the\
        constraints given the objects its expected to work on

    :param constrained_vertices: a list of constrained vertices which each has\
        constraints given to the algorithm
    :type constrained_vertices: iterable(\
        :py:class:`pacman.model.constraints.AbstractConstraint`)
    :param supported_constraints: The constraints supported
    :type supported_constraints: iterable(\
        :py:class:`pacman.model.constraints.AbstractConstraint`)
    :param abstract_constraint_type: The overall abstract c type supported
    :type abstract_constraint_type:\
        :py:class:`pacman.model.constraints.AbstractConstraint`
    :return: Nothing is returned
    :rtype: None
    :raise pacman.exceptions.PacmanInvalidParameterException: \
        When the algorithm cannot support the constraints demanded of it
    """
    for constrained_vertex in constrained_vertices:
        for c in constrained_vertex.constraints:
            if isinstance(c, abstract_constraint_type) and not \
                    _is_constraint_supported(c, supported_constraints):
                raise PacmanInvalidParameterException(
                    "constraints", c.__class__,
                    "Constraints of this class are not supported by this"
                    " algorithm")


def check_constrained_value(value, current_value):
    """ Checks that the current value and a new value match

    :param value: The value to check
    :param current_value: The existing value
    """
    if not is_equal_or_None(current_value, value):
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
    :rtype: numpy.array(uint8)
    """
    return numpy.unpackbits(
        numpy.asarray([value], dtype=">u4").view(dtype="uint8"))


def compress_from_bit_array(bit_array):
    """ Compress a bit array of 32 uint8 values, where each is a 1 or 0,\
        into a 32-bit value

    :param bit_array: The array to compress
    :type bit_array: numpy.array(uint8)
    :rtype: int
    """
    return numpy.packbits(bit_array).view(dtype=">u4")[0].item()


def compress_bits_from_bit_array(bit_array, bit_positions):
    """ Compress specific positions from a bit array of 32 uint8 value,\
        where is a 1 or 0, into a 32-bit value.

    :param bit_array: The array to extract the value from
    :type bit_array: numpy.array(uint8)
    :param bit_positions: The positions of the bits to extract, each value\
        being between 0 and 31
    :type bit_positions: numpy.array(int)
    :rtype: int
    """
    expanded_value = numpy.zeros(32, dtype="uint8")
    expanded_value[-len(bit_positions):] = bit_array[bit_positions]
    return compress_from_bit_array(expanded_value)


def is_equal_or_None(a, b):
    """ If a and b are both not None, return True iff they are equal,\
        otherwise return True
    """
    return (a is None or b is None or a == b)


def is_single(iterable):
    """ Test if there is exactly one item in the iterable
    """
    iterator = iter(iterable)

    # Test if there is a first item, if not return False
    if next(iterator, None) is None:
        return False

    # Test if there is a second item, if not return True
    if next(iterator, None) is None:
        return True

    # Otherwise return False
    return False


def md5(string):
    """ Get the MD5 hash of the given string, which is UTF-8 encoded.

    :type string: str
    :rtype: str
    """
    return hashlib.md5(string.encode()).hexdigest()


def ident(object):  # @ReservedAssignment
    """ Get the ID of the given object.

    :type object: object
    :rtype: str
    """
    return str(id(object))
