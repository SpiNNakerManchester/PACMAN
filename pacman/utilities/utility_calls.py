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
import math
from typing import Any, Iterable

import numpy

from pacman.exceptions import PacmanValueError
from pacman.model.graphs.common import Slice
from pacman.utilities.constants import BITS_IN_KEY


def expand_to_bit_array(value: int) -> numpy.ndarray:
    """
    Expand a 32-bit value in to an array of length 32 of uint8 values,
    each of which is a 1 or 0.

    :param value: The value to expand
    :returns: Bit array representing the value
    """
    return numpy.unpackbits(
        numpy.asarray([value], dtype=">u4").view(dtype="uint8"))


def compress_from_bit_array(bit_array: numpy.ndarray) -> int:
    """
    Compress a bit array of 32 uint8 values, where each is a 1 or 0,
    into a 32-bit value.

    :param bit_array: The array to compress
    :returns: integer value of the whole bit array
    """
    return numpy.packbits(bit_array).view(dtype=">u4")[0].item()


def compress_bits_from_bit_array(
        bit_array: numpy.ndarray, bit_positions: numpy.ndarray) -> int:
    """
    Compress specific positions from a bit array of 32 uint8 value,
    where is a 1 or 0, into a 32-bit value.

    :param bit_array:
        The array to extract the value from
    :param bit_positions:
        The positions of the bits to extract,
        each value being between 0 and 31
    :returns: integer value of the specified part bit array
    """
    expanded_value = numpy.zeros(BITS_IN_KEY, dtype="uint8")
    expanded_value[-len(bit_positions):] = bit_array[bit_positions]
    return compress_from_bit_array(expanded_value)


def is_equal_or_none(a: Any, b: Any) -> bool:
    """
    If a and b are both not `None`, return True if and only if they are equal,
    otherwise return True.

    :returns: True if either value is None or they are equal
    """
    return (a is None or b is None or a == b)


def is_single(iterable: Iterable[Any]) -> bool:
    """
    :returns: True if there is exactly one item in the iterable.
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


def md5(string: str) -> str:
    """
    Get the MD5 hash of the given string, which is UTF-8 encoded.

    :param string:
    :returns: the hash key
    """
    return hashlib.md5(string.encode()).hexdigest()


def get_n_bits(n_values: int) -> int:
    """
    Determine how many bits are required for the given number of values.

    :param n_values: the number of values (starting at 0)
    :return: the number of bits required to express that many values
    """
    if n_values == 0:
        return 0
    if n_values == 1:
        return 1
    return int(math.ceil(math.log2(n_values)))


def allocator_bits_needed(size: int) -> int:
    """
    Get the bits needed for the routing info allocator.

    :param size: The size to calculate the number of bits for
    :return: the number of bits required for that size
    """
    if size == 0:
        return 0
    return int(math.ceil(math.log2(size)))


def get_keys(
        base_key: int, vertex_slice: Slice,
        n_extra_bits: int = 0) -> numpy.ndarray:
    """
    :param base_key: The base key for the vertex slice
    :param vertex_slice: The slice of the vertex to get keys for
    :param n_extra_bits: Additional right shift to apply to atoms
    :returns: the keys for a given vertex slice.
    """
    indices = numpy.arange(0, vertex_slice.n_atoms) << n_extra_bits
    return base_key + indices


def is_power_of_2(v: int) -> bool:
    """
    :param v: The value to test
    :returns: True if the value is a power of 2.
    """
    return (v & (v - 1) == 0) and (v != 0)


def calc_shift(mask: int) -> int:
    """
    Calculate the shift for the given mask.

    This requires a mask where all the 1 bits are before all the zero bits

    :param mask:
    :return: The shift
    :raises PacmanValueError: If the mask does not support a clean shift
    """
    bits = expand_to_bit_array(mask)
    found_shift = False
    shift = -1000
    for i in range(BITS_IN_KEY):
        if bits[i] == 1:
            # Check all 1 come before the zeros
            if found_shift:
                raise PacmanValueError(
                    f"mask:{hex(mask)} does not support a clean shift."
                    f" It has masked bits after the unmasked bits in {bits}")
        else:
            if not found_shift:
                shift = BITS_IN_KEY - i
                found_shift = True

    if found_shift:
        return shift

    return 0


def can_shift(mask: int) -> bool:
    """
    Checks if the mask can generate a clean shift.

    :param mask:
    :return: True if cal_shift will work or False if it will error.
    """
    bits = expand_to_bit_array(mask)
    found_zeros = False
    for i in range(BITS_IN_KEY):
        if bits[i] == 1:
            # Check all 1 come before the zeros
            if found_zeros:
                return False
        else:
            found_zeros = True

    return True


def last_one(key: int) -> int:
    """
    Index of last 1 value of the key as bits

    The most significant bit is index 0

    Assumes size of key is 32 bits

    If key is zero will return -1

    :returns: index with the most significant bit being 0
    """
    last = -1
    bits = expand_to_bit_array(key)
    for i in range(BITS_IN_KEY):
        if bits[i] == 1:
            last = i
    return last


def first_one(key: int) -> int:
    """
    Index of last 1 value of the key as bits

    The most significant bit is index 0

    Assumes size of key is 32 bits

    If key is zero will return 32

    :returns: index with the most significant bit being 0
    """
    bits = expand_to_bit_array(key)
    for i in range(BITS_IN_KEY):
        if bits[i] == 1:
            return i
    return BITS_IN_KEY
