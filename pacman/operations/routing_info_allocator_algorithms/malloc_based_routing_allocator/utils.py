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

from functools import reduce
import itertools
import logging
from spinn_utilities.log import FormatAdapter
from pacman.model.routing_info import (
    BaseKeyAndMask, PartitionRoutingInfo, RoutingInfo)
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.utilities.algorithm_utilities import ElementAllocatorAlgorithm
from pacman.utilities.utility_calls import get_key_ranges
from .key_field_generator import KeyFieldGenerator

logger = FormatAdapter(logging.getLogger(__name__))


class RoutingInfoAllocator(ElementAllocatorAlgorithm):
    """ Support code for routing information allocators.

    No public methods or fields.
    """
    __slots__ = ("__routing_info")

    def __init__(self, begin, end):
        """
        :param int begin: inclusive
        :param int end: exclusive
        """
        super().__init__([(begin, end)])
        self.__routing_info = RoutingInfo()

    def _allocate_keys_and_masks(self, fixed_mask, fields, partition_n_keys,
                                 contiguous_keys=True):
        """
        :param fixed_mask:
        :type fixed_mask: int or None
        :param fields:
        :type fields: ~collections.abc.Iterable(Field) or None
        :param int partition_n_keys:
        :param bool contiguous_keys:
        :rtype: list(BaseKeyAndMask)
        :raises PacmanRouteInfoAllocationException:
            If we run out of space
        """
        # If there isn't a fixed mask, generate a fixed mask based
        # on the number of keys required
        masks_available = [fixed_mask]
        if fixed_mask is None:
            masks_available = get_possible_masks(
                partition_n_keys, contiguous_keys=contiguous_keys)

        # For each usable mask, try all of the possible keys and
        # see if a match is possible
        key, mask = self.__find_key_and_mask(
            fields, masks_available, partition_n_keys)

        # If we found a working key and mask that can be assigned,
        # Allocate them
        if key is not None:
            for base_key, n_keys in get_key_ranges(key, mask):
                self.allocate_elements(base_key, n_keys)

            # If we get here, we can assign the keys to the edges
            return [BaseKeyAndMask(base_key=key, mask=mask)]

        raise PacmanRouteInfoAllocationException(
            "Could not find space to allocate keys")

    def __find_key_and_mask(self, fields, masks_available, partition_n_keys):
        """
        :param fields:
        :type fields: ~collections.abc.Iterable(Field) or None
        :param list(int) masks_available:
        :param int partition_n_keys:
        :rtype: tuple(int,int) or tuple(None,None)
        """
        for mask in masks_available:
            logger.debug("Trying mask {} for {} keys",
                         hex(mask), partition_n_keys)

            key_generator = KeyFieldGenerator(
                mask, fields, self._free_space_tracker)
            for key in key_generator:
                logger.debug("Trying key {}", hex(key))

                # Check if all the key ranges can be allocated
                if self.__check_match(key, mask):
                    logger.debug(
                        "Matched key {} and mask {}", hex(key), hex(mask))
                    return key, mask
        return None, None

    def __check_match(self, key, mask):
        """
        :param int key:
        :param int mask:
        :rtype: bool
        """
        index = 0
        for base_key, n_keys in get_key_ranges(key, mask):
            logger.debug("Finding slot for {}, n_keys={}",
                         hex(base_key), n_keys)
            index = self._find_slot(base_key, lo=index)
            logger.debug("Slot for {} is {}", hex(base_key), index)
            if index is None:
                return False
            space = self._check_allocation(index, base_key, n_keys)
            logger.debug("Space for {} is {}", hex(base_key), space)
            if space is None:
                return False
        return True

    def _allocate_fixed_keys_and_masks(self, keys_and_masks):
        """ Allocate fixed keys and masks.

        :param ~collections.abc.Iterable(BaseKeyAndMask) keys_and_masks:
            the fixed keys and masks combos
        :raises PacmanRouteInfoAllocationException:
            If we run out of space
        """
        # If there are fixed keys and masks, allocate them
        for key_and_mask in keys_and_masks:
            # Go through the mask sets and allocate
            for key, n_keys in get_key_ranges(
                    key_and_mask.key, key_and_mask.mask):
                self.allocate_elements(key, n_keys)

    def _update_routing_objects(self, keys_and_masks, partition):
        """
        :param ~collections.abc.Iterable(BaseKeyAndMask) keys_and_masks:
        :param AbstractSingleSourcePartition partition:
        """
        # Allocate the routing information
        self.__routing_info.add_partition_info(PartitionRoutingInfo(
            keys_and_masks, partition))

    def _get_allocated_routing_info(self):
        """
        Get the routing info that we've accumulated.

        :rtype: RoutingInfo
        """
        return self.__routing_info


def get_possible_masks(n_keys, mask_width=32, contiguous_keys=True):
    """ Get the possible masks given the number of keys.

    :param int n_keys: The number of keys to generate a mask for
    :param int mask_width:
        Number of bits that are meaningful in the mask. 32 by default.
    :param bool contiguous_keys:
        True if the mask should only have zeros in the LSBs
    :return: A generator of all possible masks
    :rtype: ~collections.abc.Iterable(int)
    """
    # Starting values
    n_zeros = (n_keys - 1).bit_length()
    assert n_zeros <= mask_width
    all_ones_mask = (1 << mask_width) - 1

    # Get all possible places where the zero bits could be put; this is an
    # ideal way to do it too, as it gives us the one with the bits at the
    # bottom (the old generation algorithm) first.
    places_for_zeroes = itertools.combinations(range(mask_width), n_zeros)

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
    :param ~collections.abc.Iterable(int) bits_to_zero:
        Which bits to clear. The LSB is zero.
    :return: A single mask, with zeroes in all required places
    :rtype: int
    """
    return reduce(
        (lambda mask, bit_to_zero_out: mask & ~(1 << bit_to_zero_out)),
        bits_to_zero, all_ones_mask)
