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

import math
from spinn_utilities.abstract_base import AbstractBase
from pacman.model.resources import ElementFreeSpace
from pacman.exceptions import PacmanElementAllocationException


class ElementAllocatorAlgorithm(object, metaclass=AbstractBase):
    """ Abstract element allocator algorithm which allocates elements from\
        a pool of a given size
    """

    __slots__ = [
        # the space object for memory allocation
        "_free_space_tracker"
    ]

    def __init__(self, size_begin, size_end):
        """
        :param int size_begin:
        :param int size_end:
        """
        self._free_space_tracker = list()
        self._free_space_tracker.append(ElementFreeSpace(size_begin, size_end))

    def _allocate_elements(self, base_element_id, n_elements):
        """ Handle the allocating of space for a given set of elements

        :param int base_element_id: the first element ID to allocate
        :param int n_elements: the number of elements to allocate
        :raises PacmanRouteInfoAllocationException:
            when the ID cannot be assigned due to the number of elements
        """

        index = self._find_slot(base_element_id)
        if index is None:
            raise PacmanElementAllocationException(
                "Space for {} elements starting at {} has already "
                "been allocated".format(n_elements, base_element_id))

        # base element should be >= slot element at this point
        self.__do_allocation(index, base_element_id, n_elements)

    def _find_slot(self, base_element_id, lo=0):
        """ Find the free slot with the closest
            base element ID  <= base element using a binary search

        :param int base_element_id:
        :param int lo:
        :rtype: int or None
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

    def __do_allocation(self, index, base_element_id, n_elements):
        """ Allocate a given base element ID and number of elements into the\
            space at the given slot

        :param int index: The index of the free space slot to check
        :param int base_element_id:
            The element ID to start with; must be inside the slot
        :param int n_elements:
            The number of elements to be allocated; should be power of 2
        :raises PacmanElementAllocationException:
        """

        free_space_slot = self._free_space_tracker[index]
        if free_space_slot.start_address > base_element_id:
            raise PacmanElementAllocationException(
                "Trying to allocate a element in the wrong slot!")

        # Check if there is enough space to allocate
        space = self._check_allocation(index, base_element_id, n_elements)
        if space is None:
            raise PacmanElementAllocationException(
                "Not enough space to allocate {} elements starting at {}"
                .format(n_elements, hex(base_element_id)))

        if (free_space_slot.start_address == base_element_id and
                free_space_slot.size == n_elements):
            # If the slot exactly matches the space, remove it
            del self._free_space_tracker[index]

        elif free_space_slot.start_address == base_element_id:
            # If the slot starts with the element ID, reduce the size
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
        """ Check if there is enough space for a given set of element IDs\
            starting at a base element ID inside a given slot

        :param int index: The index of the free space slot to check
        :param int base_element_id:
            The element ID to start with; must be inside the slot
        :param int n_elements:
            The number of elements to be allocated; should be power of 2
        :rtype: int or None
        :raises PacmanElementAllocationException:
        """
        free_space_slot = self._free_space_tracker[index]
        space = (free_space_slot.size -
                 (base_element_id - free_space_slot.start_address))

        if free_space_slot.start_address > base_element_id:
            raise PacmanElementAllocationException(
                "Trying to allocate a element ID in the wrong slot!")

        # Check if there is enough space for the elements
        if space < n_elements:
            return None
        return space
