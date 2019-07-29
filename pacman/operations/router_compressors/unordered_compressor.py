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

from .abstract_compressor import AbstractCompressor
from .entry import Entry


class UnorderedCompressor(AbstractCompressor):
    """
    Routing Table compressor based on brute force.
    Finds mergable pairs to replace.

    This algorithm assumes unordered rounting tables and returns
    unordered routing tables. It can therefor be used either as the main
    compressor or as a precompressor for another that makes use of order.

    In the simplest format the algorithm is.
    For every pair of entries in the table
        If they have the same spinnaker_route
            Create a merged entry
            Check that does not intersect any entry with a different route
                Remove the two original entries
                Add the merged entry
                Start over

    A slightly optimised algorithm is:
    Split the entries into buckets based on spinnaker route
    Process the buckets one at a time
        For each entry in the buckets
            For each other entry in the bucket
                Create a merge entry
                Make sure there is no clash with an entry in another bucket
                Replace the two entries and add the merge
                Start the bucket over
            If no merge found move the entry from the bucket to the result list
        When the bucket is empty the result list becomes the bucket

    A farther optimisation is to do the whole thing in place in a single list.
    Step 1 is sort the list by route in place

    Step 2 do the compression route by route usings indexes into the array
    The array is split into 6 parts.
    0 to _previous_pointer(-1):
        Entries in buckets that have already been compressed
    _previous_pointer to _write_pointer(-1):
        Finished entries for the current bucket
    _write_pointer to left(-1);
        Unused space due to previous merges
    left to right:
        Not yet finished entries from the current bucket
    right(+ 1) to _remaining_index(-1)
        Unused space due to previous merges
    _remaining_index to max_index(-1)
        Entries in buckets not yet compressed

    Step 3 use only the entries up to _write_pointer(-1)
    """

    __slots__ = [
        # Dict (by spinnaker_route) (for current chip)
        #   of entries represented as (key, mask, defautible)
        "_all_entries",
        # The next index to write a merged/unmergable entry to
        "_write_index",
        # Inclusive index of last entry in the array (len in python)
        "_max_index",
        # Exclusive pointer to the end of the entries for previous buckets
        "_previous_index",
        # Inclusive index to the first entry for later buckets
        "_remaining_index"
    ]

    def _three_way_partition(self, low, high):
        """
        Partitions the entries between low and high into three parts

        based on: https://en.wikipedia.org/wiki/Dutch_national_flag_problem
        :param low: Lowest index to consider
        :param high: Highest index to consider
        :return: (last_index of lower, last_index_of_middle)
        """
        check = low + 1
        pivot = self._all_entries[low].spinnaker_route
        while check <= high:
            if self._all_entries[check].spinnaker_route < pivot:
                temp = self._all_entries[low]
                self._all_entries[low] = self._all_entries[check]
                self._all_entries[check] = temp
                low += 1
                check += 1
            elif self._all_entries[check].spinnaker_route > pivot:
                temp = self._all_entries[high]
                self._all_entries[high] = self._all_entries[check]
                self._all_entries[check] = temp
                high -= 1
            else:
                check += 1
        return low, check

    def _quicksort(self, low, high):
        """
        Sorts the entries in place based on route
        :param low: Inclusive lowest index to consider
        :param high: Inclusive highest index to consider
        """
        if low < high:
            left, right = self._three_way_partition(low, high)
            self._quicksort(low, left - 1)
            self._quicksort(right, high)

    def _find_merge(self, left, index):
        """
        Attempt to find a merge between the left entry and the index entry

        Creates a merge and then checks it does not interesct with entries
        with different routes.

        If no intersect detected entry[left] is replaced with the merge

        :param left: Index of Entry to merge and replace if possible
        :param index: Index of entry to merge with
        :return: True if and only if a merge was found and done
        """
        m_key, m_mask, defaultable = self.merge(
            self._all_entries[left], self._all_entries[index])
        for check in range(self._previous_index):
            if self.intersect(
                    self._all_entries[check].key,
                    self._all_entries[check].mask,
                    m_key, m_mask):
                return False
        for check in range(self._remaining_index, self._max_index + 1):
            if self.intersect(
                    self._all_entries[check].key,
                    self._all_entries[check].mask,
                    m_key, m_mask):
                return False
        self._all_entries[left] = Entry(
            m_key, m_mask, defaultable,
            self._all_entries[left].spinnaker_route)
        return True

    def _compress_by_route(self, left, right):
        """
        Compresses the entries between left and right

        :param left: Inclusive index of first entry to merge
        :param right: Inclusive index of last entry to merge
        """
        while left < right:
            index = left + 1
            while index <= right:
                merged = self._find_merge(left, index)
                if merged:
                    self._all_entries[index] = self._all_entries[right]
                    # Setting None not needed but easier when debugging
                    # self._all_entries[right] = None
                    right -= 1
                    break

                index += 1
            if not merged:
                self._all_entries[self._write_index] = self._all_entries[left]
                self._write_index += 1
                left += 1
        if left == right:
            self._all_entries[self._write_index] = self._all_entries[left]
            # Setting None not needed but easier when debugging
            # if left != self._write_pointer:
            #    self._all_entries[left] = None
            self._write_index += 1

    def compress_table(self, router_table):
        """
        Compresses all the entries for a single table.

        Compressed the entries for this unordered table
        returning a new table with possibly fewer entries but still unordered

        :param router_table: Original Routing table for a single chip
        :type router_table:  MulticastRoutingTable
        :return: Compressed routing table for the same chip
        :rtype:  MulticastRoutingTable
        """

        # Split the entries into buckets based on spinnaker_route
        self._all_entries = []
        for entry in router_table.multicast_routing_entries:
            self._all_entries.append(
                Entry.from_MulticastRoutingEntry(entry))
        self._quicksort(0, len(self._all_entries) - 1)

        self._write_index = 0
        self._max_index = len(self._all_entries) - 1
        self._previous_index = 0

        left = 0
        while left < self._max_index:
            right = left
            while (right < len(self._all_entries) - 1 and
                   self._all_entries[right+1].spinnaker_route
                   == self._all_entries[left].spinnaker_route):
                right += 1
            self._remaining_index = right + 1
            self._compress_by_route(left, right)
            left = right + 1
            self._previous_index = self._write_index

        return self._all_entries[0:self._write_index]
