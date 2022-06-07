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

import hashlib
import numpy
import math
from pacman.exceptions import (
    PacmanInvalidParameterException, PacmanValueError)


def locate_constraints_of_type(constraints, constraint_type):
    """ Locates all constraints of a given type out of a list

    :param iterable(AbstractConstraint) constraints: The constraints to filter
    :param type(AbstractConstraint) constraint_type:
        The type of constraints to return
    :return: The constraints of constraint_type that are found in the
        constraints given
    :rtype: iterable(AbstractConstraint)
    """
    return [c for c in constraints if isinstance(c, constraint_type)]


def locate_first_constraint_of_type(constraints, constraint_type):
    """ Locates the first constraint of a given type out of a list

    :param iterable(AbstractConstraint) constraints:
        The constraints to select from
    :param type(AbstractConstraint) constraint_type:
        The type of constraints to return
    :return: The first constraint of `constraint_type` that was found in the
        constraints given
    :rtype: AbstractConstraint
    :raises PacmanInvalidParameterException:
        If no such constraint is present
    """
    for constraint in constraints:
        if isinstance(constraint, constraint_type):
            return constraint
    raise PacmanInvalidParameterException(
        "constraints", constraint_type.__class__,
        "Constraints of this class are not present")


def _is_constraint_supported(constraint, supported_constraints):
    """
    :param AbstractConstraint constraint:
    :param list(type(AbstractConstraint)) supported_constraints:
    :rtype: bool
    """
    return any(isinstance(constraint, supported_constraint)
               for supported_constraint in supported_constraints)


def check_algorithm_can_support_constraints(
        constrained_vertices, supported_constraints, abstract_constraint_type):
    """ Helper method to find out if an algorithm can support all the
        constraints given the objects its expected to work on

    :param list(AbstractVertex) constrained_vertices:
        a list of constrained vertices which each has constraints given to the
        algorithm
    :param list(type(AbstractConstraint)) supported_constraints:
        The constraints supported
    :param type(AbstractConstraint) abstract_constraint_type:
        The overall abstract c type supported
    :raise PacmanInvalidParameterException:
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
    """ Expand a 32-bit value in to an array of length 32 of uint8 values,
        each of which is a 1 or 0

    :param int value: The value to expand
    :rtype: ~numpy.ndarray(uint8)
    """
    return numpy.unpackbits(
        numpy.asarray([value], dtype=">u4").view(dtype="uint8"))


def compress_from_bit_array(bit_array):
    """ Compress a bit array of 32 uint8 values, where each is a 1 or 0,
        into a 32-bit value

    :param ~numpy.ndarray(uint8) bit_array: The array to compress
    :rtype: int
    """
    return numpy.packbits(bit_array).view(dtype=">u4")[0].item()


def compress_bits_from_bit_array(bit_array, bit_positions):
    """ Compress specific positions from a bit array of 32 uint8 value,\
        where is a 1 or 0, into a 32-bit value.

    :param ~numpy.ndarray(uint8) bit_array:
        The array to extract the value from
    :param ~numpy.ndarray(int) bit_positions:
        The positions of the bits to extract,
        each value being between 0 and 31
    :rtype: int
    """
    expanded_value = numpy.zeros(32, dtype="uint8")
    expanded_value[-len(bit_positions):] = bit_array[bit_positions]
    return compress_from_bit_array(expanded_value)


def is_equal_or_None(a, b):
    """ If a and b are both not None, return True iff they are equal,\
        otherwise return True

    :rtype: bool
    """
    return (a is None or b is None or a == b)


def is_single(iterable):
    """ Test if there is exactly one item in the iterable

    :rtype: bool
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

    :param str string:
    :rtype: str
    """
    return hashlib.md5(string.encode()).hexdigest()


def get_key_ranges(key, mask):
    """ Get a generator of base_key, n_keys pairs that represent ranges
        allowed by the mask.

    :param int key: The base key
    :param int mask: The mask
    :rtype: iterable(tuple(int,int))
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
    for value in range(n_sets):
        generated_key = numpy.copy(unwrapped_key)
        generated_key[remaining_zeros] = \
            expand_to_bit_array(value)[-len(remaining_zeros):]
        yield compress_from_bit_array(generated_key), n_keys


def get_n_bits(n_values):
    """ Determine how many bits are required for the given number of values

    :param int n_values: the number of values (starting at 0)
    :return: the number of bits required to express that many values
    :rtype: int
    """
    if n_values == 0:
        return 0
    if n_values == 1:
        return 1
    return int(math.ceil(math.log(n_values, 2)))


def get_field_based_keys(key, vertex_slice):
    """ Translate a vertex slice with potentially multiple dimensions into
        a list of keys, one for each atom of the vertex, by putting the values
        into fields of the keys based on the shape of the slice.

    :param int key: The base key
    :param Slice vertex_slice: The slice to translate
    :rtype: list(int)
    """

    # Find the size of field required for each coordinate, and the shift
    # required to get to this field position (the first field has a shift
    # of 0)
    field_sizes = numpy.array([get_n_bits(n) for n in vertex_slice.shape])
    shifts = numpy.concatenate(([0], numpy.cumsum(field_sizes[:-1])))

    # Convert each atom into x, y coordinates based on shape
    # This uses numpy.unravel_index, the result of which needs to be
    # made into an array (it is a list of tuples) and transposed (it
    # gives the coordinates separately per axis)
    coords = numpy.array(numpy.unravel_index(
        numpy.arange(vertex_slice.n_atoms),
        vertex_slice.shape, order='F')).T

    # We now left shift each coordinate into its field and add them up to
    # get the key
    keys = numpy.sum(numpy.left_shift(coords, shifts), axis=1)

    # The final result is the above with the base key added
    return keys + key


def get_field_based_index(base_key, vertex_slice):
    """ Map field based keys back to indices

    :param int base_key: The base key
    :param Slice vertex_slice: The slice to translate
    :rtype: dict(int,int)
    """
    # Get the field based keys
    field_based_keys = get_field_based_keys(base_key, vertex_slice)

    # Inverse the index
    return {
        key: i
        for i, key in enumerate(field_based_keys)
    }
