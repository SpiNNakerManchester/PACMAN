import math
import itertools
from six.moves import reduce, xrange


def get_possible_masks(n_keys):
    """ Get the possible masks given the number of keys.

    :param n_keys: The number of keys to generate a mask for
    :type n_keys: int
    :return: A generator of all possible masks
    :rtype: iterable(int)
    """
    # Starting values
    n_bits = 32
    n_zeros = int(math.ceil(math.log(n_keys, 2)))
    assert n_zeros <= n_bits
    all_ones_mask = (1 << n_bits) - 1

    # Get all possible places where the zero bits could be put; this is an
    # ideal way to do it too, as it gives us the one with the bits at the
    # bottom (the old generation algorithm) first.
    places_for_zeroes = itertools.combinations(xrange(n_bits), n_zeros)

    # Convert the selected places for zero bits into an iterable of masks
    return (
        zero_out_bits(all_ones_mask, zero_bits)
        for zero_bits in places_for_zeroes)


def zero_out_bits(all_ones_mask, bits_to_zero):
    """ Takes a mask (with all interesting bits set to 1) and zeroes out the\
        bits at the given indices.

    :param all_ones_mask: Initial mask
    :type all_ones_mask: int
    :param bits_to_zero: Which bits to clear. The LSB is zero.
    :type bits_to_zero: iterable(int)
    :return: A single mask, with zeroes in all required places
    :rtype: int
    """
    return reduce(
        (lambda mask, bit_to_zero_out: mask & ~(1 << bit_to_zero_out)),
        bits_to_zero, all_ones_mask)
