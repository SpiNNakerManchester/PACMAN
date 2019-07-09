import itertools
from six.moves import reduce, xrange


def get_possible_masks(n_keys, mask_width=32, contiguous_keys=True):
    """ Get the possible masks given the number of keys.

    :param n_keys: The number of keys to generate a mask for
    :type n_keys: int
    :param mask_width: \
        Number of bits that are meaningful in the mask. 32 by default.
    :param mask_width: int
    :param contiguous_keys: \
        True if the mask should only have zeros in the LSBs
    :return: A generator of all possible masks
    :rtype: iterable(int)
    """
    # Starting values
    n_zeros = n_keys.bit_length()
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
