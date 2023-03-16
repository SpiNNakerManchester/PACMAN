# Copyright (c) 2014 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import numpy
import math


def expand_to_bit_array(value):
    """
    Expand a 32-bit value in to an array of length 32 of uint8 values,
    each of which is a 1 or 0

    :param int value: The value to expand
    :rtype: ~numpy.ndarray(uint8)
    """
    return numpy.unpackbits(
        numpy.asarray([value], dtype=">u4").view(dtype="uint8"))


def compress_from_bit_array(bit_array):
    """
    Compress a bit array of 32 uint8 values, where each is a 1 or 0,
    into a 32-bit value

    :param ~numpy.ndarray(uint8) bit_array: The array to compress
    :rtype: int
    """
    return numpy.packbits(bit_array).view(dtype=">u4")[0].item()


def compress_bits_from_bit_array(bit_array, bit_positions):
    """
    Compress specific positions from a bit array of 32 uint8 value,
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
    """
    If a and b are both not `None`, return True iff they are equal,
    otherwise return True.

    :rtype: bool
    """
    return (a is None or b is None or a == b)


def is_single(iterable):
    """
    Test if there is exactly one item in the iterable.

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
    """
    Get the MD5 hash of the given string, which is UTF-8 encoded.

    :param str string:
    :rtype: str
    """
    return hashlib.md5(string.encode()).hexdigest()


def get_key_ranges(key, mask):
    """
    Get a generator of base_key, n_keys pairs that represent ranges
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
    """
    Determine how many bits are required for the given number of values.

    :param int n_values: the number of values (starting at 0)
    :return: the number of bits required to express that many values
    :rtype: int
    """
    if n_values == 0:
        return 0
    if n_values == 1:
        return 1
    return int(math.ceil(math.log2(n_values)))


def get_field_based_keys(key, vertex_slice, shift=0):
    """
    Translate a vertex slice with potentially multiple dimensions into
    a list of keys, one for each atom of the vertex, by putting the values
    into fields of the keys based on the shape of the slice.

    :param int key: The base key
    :param Slice vertex_slice: The slice to translate
    :param int shift:
        The left shift to apply to the atom key before adding to the key. Can
        be used to make space for additional information at the bottom of the
        key.
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

    # Do any final shifting as required (zero shift is valid but does nothing)
    if shift:
        keys = numpy.left_shift(keys, shift)

    # The final result is the above with the base key added
    return keys + key


def get_field_based_index(base_key, vertex_slice, shift=0):
    """
    Map field based keys back to indices.

    :param int base_key: The base key
    :param Slice vertex_slice: The slice to translate
    :param int shift:
        The left shift to apply to the atom key before adding to the key. Can
        be used to make space for additional information at the bottom of the
        key.
    :rtype: dict(int,int)
    """
    # Get the field based keys
    field_based_keys = get_field_based_keys(base_key, vertex_slice, shift)

    # Inverse the index
    return {
        key: i
        for i, key in enumerate(field_based_keys)
    }


def get_n_bits_for_fields(field_sizes):
    """
    Get the number of bits required for the fields in the vertex slice.

    :param iterable(int) field_sizes: The sizes each of the fields
    :rtype: int
    """
    field_size = [get_n_bits(n) for n in field_sizes]
    return sum(field_size)


def allocator_bits_needed(size):
    """
    Get the bits needed for the routing info allocator.

    :param int size: The size to calculate the number of bits for
    :return: the number of bits required for that size
    :rtype: int
    """
    if size == 0:
        return 0
    return int(math.ceil(math.log2(size)))
