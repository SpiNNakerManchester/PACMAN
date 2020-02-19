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

import itertools
from six.moves import reduce, xrange


def get_possible_masks(n_keys, mask_width=32, contiguous_keys=True):
    """ Get the possible masks given the number of keys.

    :param int n_keys: The number of keys to generate a mask for
    :param int mask_width:
        Number of bits that are meaningful in the mask. 32 by default.
    :param bool contiguous_keys:
        True if the mask should only have zeros in the LSBs
    :return: A generator of all possible masks
    :rtype: iterable(int)
    """
    # Starting values
    n_zeros = (n_keys - 1).bit_length()
    assert n_zeros <= mask_width
    all_ones_mask = (1 << mask_width) - 1

    # Get all possible places where the zero bits could be put; this is an
    # ideal way to do it too, as it gives us the one with the bits at the
    # bottom (the old generation algorithm) first.
    places_for_zeroes = itertools.combinations(xrange(mask_width), n_zeros)

    # If the keys are all contiguous, you can only have one possible mask,
    # which is the first one
    if contiguous_keys:
        zero_bits = next(places_for_zeroes)
        return [zero_out_bits(all_ones_mask, zero_bits)]

    # Convert the selected places for zero bits into an iterable of masks
    return (
        zero_out_bits(all_ones_mask, zero_bits)
        for zero_bits in places_for_zeroes)


def zero_out_bits(all_ones_mask, bits_to_zero):
    """ Takes a mask (with all interesting bits set to 1) and zeroes out the\
        bits at the given indices.

    :param int all_ones_mask: Initial mask
    :param iterable(int) bits_to_zero: Which bits to clear. The LSB is zero.
    :return: A single mask, with zeroes in all required places
    :rtype: int
    """
    return reduce(
        (lambda mask, bit_to_zero_out: mask & ~(1 << bit_to_zero_out)),
        bits_to_zero, all_ones_mask)
