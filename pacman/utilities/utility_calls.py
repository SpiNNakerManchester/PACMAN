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
from typing import Any, Iterable, Tuple
import numpy
from pacman.model.graphs.common import Slice


def expand_to_bit_array(value: int) -> numpy.ndarray:
    """
    Expand a 32-bit value in to an array of length 32 of uint8 values,
    each of which is a 1 or 0.

    :param int value: The value to expand
    :rtype: ~numpy.ndarray(uint8)
    """
    return numpy.unpackbits(
        numpy.asarray([value], dtype=">u4").view(dtype="uint8"))


def compress_from_bit_array(bit_array: numpy.ndarray) -> int:
    """
    Compress a bit array of 32 uint8 values, where each is a 1 or 0,
    into a 32-bit value.

    :param ~numpy.ndarray(uint8) bit_array: The array to compress
    :rtype: int
    """
    return numpy.packbits(bit_array).view(dtype=">u4")[0].item()


def compress_bits_from_bit_array(
        bit_array: numpy.ndarray, bit_positions: numpy.ndarray) -> int:
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


def is_equal_or_none(a: Any, b: Any) -> bool:
    """
    If a and b are both not `None`, return True if and only if they are equal,
    otherwise return True.

    :rtype: bool
    """
    return (a is None or b is None or a == b)


def is_single(iterable: Iterable[Any]) -> bool:
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


def md5(string: str) -> str:
    """
    Get the MD5 hash of the given string, which is UTF-8 encoded.

    :param str string:
    :rtype: str
    """
    return hashlib.md5(string.encode()).hexdigest()


def get_key_ranges(key: int, mask: int) -> Iterable[Tuple[int, int]]:
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


def get_n_bits(n_values: int) -> int:
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


def allocator_bits_needed(size: int) -> int:
    """
    Get the bits needed for the routing info allocator.

    :param int size: The size to calculate the number of bits for
    :return: the number of bits required for that size
    :rtype: int
    """
    if size == 0:
        return 0
    return int(math.ceil(math.log2(size)))


def get_keys(
        base_key: int, vertex_slice: Slice,
        n_extra_bits: int = 0) -> numpy.ndarray:
    """
    Get the keys for a given vertex slice.

    :param int base_key: The base key for the vertex slice
    :param Slice vertex_slice: The slice of the vertex to get keys for
    :param int n_extra_bits: Additional right shift to apply to atoms

    :rtype: iterable(int)
    """
    indices = numpy.arange(0, vertex_slice.n_atoms) << n_extra_bits
    return base_key + indices


def is_power_of_2(v: int) -> bool:
    """
    Determine if a value is a power of 2.

    :param int v: The value to test
    :rtype: bool
    """
    return (v & (v - 1) == 0) and (v != 0)
