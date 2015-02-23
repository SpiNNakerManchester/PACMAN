import math
import numpy

from pacman.model.constraints.abstract_key_allocator_constraint import \
    AbstractKeyAllocatorConstraint
from pacman.model.constraints.key_allocator_same_keys_constraint import \
    KeyAllocatorSameKeysConstraint
from pacman.model.constraints.key_allocator_fixed_mask_constraint import \
    KeyAllocatorFixedMaskConstraint
from pacman.model.constraints.key_allocator_fixed_key_and_mask_constraint \
    import KeyAllocatorFixedKeyAndMaskConstraint
from pacman.model.constraints.key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint

from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.key_and_mask import KeyAndMask
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo

from pacman.operations.routing_info_allocator_algorithms.\
    abstract_routing_info_allocator_algorithm import \
    AbstractRoutingInfoAllocatorAlgorithm
from pacman.operations.routing_info_allocator_algorithms.\
    malloc_based_routing_allocator.free_space import FreeSpace

from pacman.utilities import utility_calls
from pacman.exceptions import PacmanRouteInfoAllocationException

import logging
logger = logging.getLogger(__name__)


class MallocBasedRoutingInfoAllocator(AbstractRoutingInfoAllocatorAlgorithm):
    """ A Routing Info Allocation Allocator algorithm that keeps track of
        free keys and attempts to allocate them as requested
    """

    def __init__(self):
        AbstractRoutingInfoAllocatorAlgorithm.__init__(self)
        self._supported_constraints.append(KeyAllocatorSameKeysConstraint)
        self._supported_constraints.append(KeyAllocatorFixedMaskConstraint)
        self._supported_constraints.append(
            KeyAllocatorFixedKeyAndMaskConstraint)
        self._supported_constraints.append(
            KeyAllocatorContiguousRangeContraint)

        self._free_space_tracker = list()
        self._free_space_tracker.append(FreeSpace(0, math.pow(2, 32)))

    def _find_slot(self, base_key, lo=0):
        """ Find the free slot with the closest key <= base_key using a binary
            search
        """
        hi = len(self._free_space_tracker) - 1
        while lo < hi:
            mid = int(math.ceil(float(lo + hi) / 2.0))
            free_space_slot = self._free_space_tracker[mid]

            if free_space_slot.start_address > base_key:
                hi = mid - 1
            else:
                lo = mid

        # If we have gone off the end of the array, we haven't found a slot
        if (lo >= len(self._free_space_tracker) or hi < 0
                or self._free_space_tracker[lo].start_address > base_key):
            return None
        return lo

    def _allocate_keys(self, base_key, n_keys):
        """ Handle the allocating of space for a given set of keys

        :param base_key: the first key to allocate
        :param n_keys: the number of keys to allocate
        :raises: PacmanRouteInfoAllocationException when the key cannot be\
                    assigned with the given number of keys
        """

        index = self._find_slot(base_key)
        if index is None:
            raise PacmanRouteInfoAllocationException(
                "Space for {} keys starting at {} has already been allocated"
                .format(n_keys, base_key))

        # base_key should be >= slot key at this point
        self._do_allocation(index, base_key, n_keys)

    def _check_allocation(self, index, base_key, n_keys):
        """ Check if there is enough space for a given set of keys
            starting at a base key inside a given slot

        :param index: The index of the free space slot to check
        :param base_key: The key to start with - must be inside the slot
        :param n_keys: The number of keys to be allocated -\
                       should be power of 2
        """
        free_space_slot = self._free_space_tracker[index]
        space = (free_space_slot.size
                 - (base_key - free_space_slot.start_address))

        if free_space_slot.start_address > base_key:
            raise PacmanRouteInfoAllocationException(
                "Trying to allocate a key in the wrong slot!")
        if n_keys == 0 or (n_keys & (n_keys - 1)) != 0:
            raise PacmanRouteInfoAllocationException(
                "Trying to allocate {} keys, which is not a power of 2"
                .format(n_keys))

        # Check if there is enough space for the keys
        if space < n_keys:
            return None
        return space

    def _do_allocation(self, index, base_key, n_keys):
        """ Allocate a given base key and number of keys into the space
            at the given slot

        :param index: The index of the free space slot to check
        :param base_key: The key to start with - must be inside the slot
        :param n_keys: The number of keys to be allocated -\
                       should be power of 2
        """

        free_space_slot = self._free_space_tracker[index]
        if free_space_slot.start_address > base_key:
            raise PacmanRouteInfoAllocationException(
                "Trying to allocate a key in the wrong slot!")
        if n_keys == 0 or (n_keys & (n_keys - 1)) != 0:
            raise PacmanRouteInfoAllocationException(
                "Trying to allocate {} keys, which is not a power of 2"
                .format(n_keys))

        # Check if there is enough space to allocate
        space = self._check_allocation(index, base_key, n_keys)
        if space is None:
            raise PacmanRouteInfoAllocationException(
                "Not enough space to allocate {} keys starting at {}".format(
                    n_keys, hex(base_key)))

        if (free_space_slot.start_address == base_key
                and free_space_slot.size == n_keys):

            # If the slot exactly matches the space, remove it
            del self._free_space_trackerp[index]

        elif free_space_slot.start_address == base_key:

            # If the slot starts with the key, reduce the size
            self._free_space_tracker[index] = FreeSpace(
                free_space_slot.start_address + n_keys,
                free_space_slot.size - n_keys)

        elif space == n_keys:

            # If the space at the end exactly matches the spot, reduce the size
            self._free_space_tracker[index] = FreeSpace(
                free_space_slot.start_address,
                free_space_slot.size - n_keys)

        else:

            # Otherwise, the allocation lies in the middle of the region:
            # First, reduce the size of the space before the allocation
            self._free_space_tracker[index] = FreeSpace(
                free_space_slot.start_address,
                base_key - free_space_slot.start_address)

            # Then add a new space after the allocation
            self._free_space_tracker.insert(index + 1, FreeSpace(
                base_key + n_keys,
                free_space_slot.start_address + free_space_slot.size
                - (base_key + n_keys)))

    @staticmethod
    def _get_key_ranges(key, mask):
        """ Get a generator of base_key, n_keys pairs that represent ranges
            allowed by the mask

        :param key: The base key
        :param mask: The mask
        """
        unwrapped_mask = numpy.unpackbits(
            numpy.asarray([mask], dtype=">u4").view(dtype="uint8"))
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
        unwrapped_key = numpy.unpackbits(
            numpy.asarray([key], dtype=">u4").view(dtype="uint8"))
        for value in range(n_sets):
            generated_key = numpy.copy(unwrapped_key)
            unwrapped_value = numpy.unpackbits(
                numpy.asarray([value], dtype=">u4")
                     .view(dtype="uint8"))[-len(remaining_zeros):]
            generated_key[remaining_zeros] = unwrapped_value
            yield numpy.packbits(generated_key).view(dtype=">u4")[0], n_keys

    def _get_possible_keys(self, mask):
        """ Get a generator of all possible keys such that key & mask == key

        :param mask: The mask to find the valid keys from
        """
        # Get the position of the ones in the mask - assume 32-bits
        unwrapped_mask = numpy.unpackbits(
            numpy.asarray([mask], dtype=">u4").view(dtype="uint8"))
        ones = numpy.where(unwrapped_mask == 1)[0]
        n_zeros = 32 - len(ones)

        # We now know how many possible keys there are - 2^n_ONES
        n_keys = 2 ** len(ones)
        print("Mask", hex(mask), "is valid for", n_keys, "keys")

        # Get the first valid key >= first space start address
        min_key = self._free_space_tracker[0].start_address
        if min_key & mask != min_key:
            min_key = ((self._free_space_tracker[0].start_address + n_keys)
                       & mask)
        min_value = min_key / (2 ** n_zeros)
        print("first valid key for mask", hex(mask), "is", hex(min_key),
                     "which is key number", min_value)

        # Generate up to 2^len(ones) keys
        for value in range(min_value, n_keys):
            key = numpy.zeros(32, dtype="uint8")
            unwrapped_value = numpy.unpackbits(
                numpy.asarray([value], dtype=">u4")
                     .view(dtype="uint8"))[-len(ones):]
            key[ones] = unwrapped_value
            yield numpy.packbits(key).view(dtype=">u4")[0]

    @staticmethod
    def _get_possible_masks(n_keys, is_contiguous):
        """ Get the possible masks given the number of keys

        :param n_keys: The number of keys to generate a mask for
        :param is_contiguous: True if the keys should be contiguous
        """

        # TODO: Generate all the masks - currently only the obvious
        # mask with the zeros at the bottom is generated but the zeros
        # could actually be anywhere
        n_zeros = int(math.ceil(math.log(n_keys, 2)))
        n_ones = 32 - n_zeros
        return [(((1 << n_ones) - 1) << n_zeros)]

    def _allocate_fixed_keys_and_masks(self, keys_and_masks, fixed_mask):

        # If there are fixed keys and masks, allocate them
        for key_and_mask in keys_and_masks:

            # If there is a fixed mask, check it doesn't clash
            if fixed_mask is not None and fixed_mask != key_and_mask.mask:
                raise PacmanRouteInfoAllocationException(
                    "Cannot meet conflicting constraints")

            # Go through the mask sets and allocate
            for key, n_keys in self._get_key_ranges(
                    key_and_mask.key, key_and_mask.mask):
                self._allocate_keys(key, n_keys)

    def _allocate_keys_and_masks(self, fixed_mask, edge_n_keys, is_contiguous):

        # If there isn't a fixed mask, generate a fixed mask based
        # on the number of keys required
        masks_available = [fixed_mask]
        if fixed_mask is None:
            masks_available = self._get_possible_masks(edge_n_keys,
                                                       is_contiguous)

        # For each usable mask, try all of the possible keys and
        # see if a match is possible
        mask_found = None
        key_found = None
        for mask in masks_available:

            key_found = None
            for key in self._get_possible_keys(mask):

                # Check if all the key ranges can be allocated
                matched_all = True
                index = 0
                for (base_key, n_keys) in self._get_key_ranges(
                        key, mask):
                    logger.debug("Finding slot for", hex(base_key))
                    index = self._find_slot(base_key, lo=index)
                    logger.debug("Slot for", hex(base_key), "is", index)
                    if index is None:
                        matched_all = False
                        break
                    space = self._check_allocation(index, base_key,
                                                   n_keys)
                    logger.debug("Space for", hex(base_key), "is", space)
                    if space is None:
                        matched_all = False
                        break

                if matched_all:
                    logger.debug("Matched key", hex(key))
                    key_found = key
                    break

            # If we found a matching key, store the mask that worked
            if key_found is not None:
                logger.debug("Matched mask", hex(mask))
                mask_found = mask
                break

        # If we found a working key and mask that can be assigned,
        # Allocate them
        if key_found is not None and mask_found is not None:
            for (base_key, n_keys) in self._get_key_ranges(
                    key_found, mask):
                self._allocate_keys(base_key, n_keys)

            # If we get here, we can assign the keys to the edges
            keys_and_masks = list([KeyAndMask(key=key_found,
                                              mask=mask)])
            return keys_and_masks

        raise PacmanRouteInfoAllocationException(
            "Could not find space to allocate keys")

    def allocate_routing_info(self, subgraph, placements, n_keys_map):

        # check that this algorithm supports the constraints
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=subgraph.subedges,
            supported_constraints=self._supported_constraints,
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # Get the partitioned edges grouped by those that require the same key
        same_key_groups = self._get_edge_groups(subgraph)

        # Go through the groups and allocate keys
        routing_infos = RoutingInfo()
        for group in same_key_groups:

            # Check how many keys are needed for the edges of the group
            edge_n_keys = None
            for edge in group:
                n_keys = n_keys_map.n_keys_for_partitioned_edge(edge)
                if edge_n_keys is None:
                    edge_n_keys = n_keys
                elif edge_n_keys != n_keys:
                    raise PacmanRouteInfoAllocationException(
                        "Two edges require the same keys but request a"
                        " different number of keys")

            # Get any fixed keys and masks from the group and attempt to
            # allocate them
            keys_and_masks = self._get_fixed_key_and_mask(group)
            fixed_mask = self._get_fixed_mask(group)

            if keys_and_masks is not None:

                self._allocate_fixed_keys_and_masks(keys_and_masks, fixed_mask)
            else:

                keys_and_masks = self._allocate_keys_and_masks(
                    fixed_mask, edge_n_keys, self._is_contiguous_range(group))

            # Allocate the routing information
            for edge in group:
                routing_infos.add_subedge_info(
                    SubedgeRoutingInfo(keys_and_masks, edge))

        return routing_infos
