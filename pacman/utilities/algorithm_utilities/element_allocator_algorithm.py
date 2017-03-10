# pacman imports
from pacman.model.resources import ElementFreeSpace
from pacman import exceptions

# general imports
from abc import ABCMeta
from six import add_metaclass
import math


@add_metaclass(ABCMeta)
class ElementAllocatorAlgorithm(object):
    """ Abstract element allocator algorithm which allocates elements from\
        a pool of a given size
    """

    __slots__ = [
        # the space object for memory allocation
        "_free_space_tracker"
    ]

    def __init__(self, size_begin, size_end):
        self._free_space_tracker = list()
        self._free_space_tracker.append(ElementFreeSpace(size_begin, size_end))

    def _allocate_elements(self, base_element_id, n_elements):
        """ Handle the allocating of space for a given set of elements

        :param base_element_id: the first element id to allocate
        :param n_elements: the number of elements to allocate
        :raises: PacmanRouteInfoAllocationException when the element id\
                    cannot be assigned with the given number of elements
        """

        index = self._find_slot(base_element_id)
        if index is None:
            raise exceptions.PacmanElementAllocationException(
                "Space for {} elements starting at {} has already "
                "been allocated".format(n_elements, base_element_id))

        # base element should be >= slot element at this point
        self._do_allocation(index, base_element_id, n_elements)

    def _find_slot(self, base_element_id, lo=0):
        """ Find the free slot with the closest\
            base element id  <= base element using a binary search
        """
        hi = len(self._free_space_tracker) - 1
        while lo < hi:
            mid = int(math.ceil(float(lo + hi) / 2.0))
            free_space_slot = self._free_space_tracker[mid]

            if free_space_slot.start_address > base_element_id:
                hi = mid - 1
            else:
                lo = mid

        # If we have gone off the end of the array, we haven't found a slot
        if (lo >= len(self._free_space_tracker) or hi < 0 or
                self._free_space_tracker[lo].start_address > base_element_id):
            return None
        return lo

    def _do_allocation(self, index, base_element_id, n_elements):
        """ Allocate a given base element id and number of elements into the\
            space at the given slot

        :param index: The index of the free space slot to check
        :param base_element_id: The element id to start with - must be\
                    inside the slot
        :param n_elements: The number of elements to be allocated -\
                    should be power of 2
        """

        free_space_slot = self._free_space_tracker[index]
        if free_space_slot.start_address > base_element_id:
            raise exceptions.PacmanElementAllocationException(
                "Trying to allocate a element in the wrong slot!")

        # Check if there is enough space to allocate
        space = self._check_allocation(index, base_element_id, n_elements)
        if space is None:
            raise exceptions.PacmanElementAllocationException(
                "Not enough space to allocate {} elements starting at {}"
                .format(n_elements, hex(base_element_id)))

        if (free_space_slot.start_address == base_element_id and
                free_space_slot.size == n_elements):

            # If the slot exactly matches the space, remove it
            del self._free_space_tracker[index]

        elif free_space_slot.start_address == base_element_id:

            # If the slot starts with the element id, reduce the size
            self._free_space_tracker[index] = ElementFreeSpace(
                free_space_slot.start_address + n_elements,
                free_space_slot.size - n_elements)

        elif space == n_elements:

            # If the space at the end exactly matches the spot, reduce the size
            self._free_space_tracker[index] = ElementFreeSpace(
                free_space_slot.start_address,
                free_space_slot.size - n_elements)

        else:

            # Otherwise, the allocation lies in the middle of the region:
            # First, reduce the size of the space before the allocation
            self._free_space_tracker[index] = ElementFreeSpace(
                free_space_slot.start_address,
                base_element_id - free_space_slot.start_address)

            # Then add a new space after the allocation
            self._free_space_tracker.insert(index + 1, ElementFreeSpace(
                base_element_id + n_elements,
                free_space_slot.start_address + free_space_slot.size -
                (base_element_id + n_elements)))

    def _check_allocation(self, index, base_element_id, n_elements):
        """ Check if there is enough space for a given set of element ids
            starting at a base element id inside a given slot

        :param index: The index of the free space slot to check
        :param base_element_id: The element id to start with -\
                    must be inside the slot
        :param n_elements: The number of elements to be allocated -\
                    should be power of 2
        """
        free_space_slot = self._free_space_tracker[index]
        space = (free_space_slot.size -
                 (base_element_id - free_space_slot.start_address))

        if free_space_slot.start_address > base_element_id:
            raise exceptions.PacmanElementAllocationException(
                "Trying to allocate a element id in the wrong slot!")

        # Check if there is enough space for the elements
        if space < n_elements:
            return None
        return space
