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

from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)
from spinn_machine import MulticastRoutingEntry
from .entry import Entry


class UnorderedCompressor(object):
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
        # Max length below which the algorithm should stop compressing
        "_target_length",
        # The next index to write a merged/unmergable entry to
        "_write_index",
        # Inclusive index of last entry in the array (len in python)
        "_max_index",
        # Exclusive pointer to the end of the entries for previous buckets
        "_previous_index",
        # Inclusive index to the first entry for later buckets
        "_remaining_index"

    ]

    def __call__(self, router_tables, target_length=None):
        if target_length is None:
            self._target_length = 0  # Compress as much as you can
        else:
            self._target_length = target_length
        # create progress bar
        progress = ProgressBar(
            router_tables.routing_tables, "PreCompressing routing Tables")
        return self.compress_tables(router_tables, progress)

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

    def intersect(self, key_a, mask_a, key_b, mask_b):
        """
        Return if key-mask pairs intersect (i.e., would both match some of the
        same keys).
        For example, the key-mask pairs ``00XX`` and ``001X`` both match the
        keys ``0010`` and ``0011`` (i.e., they do intersect)::
            >>> intersect(0b0000, 0b1100, 0b0010, 0b1110)
            True
        But the key-mask pairs ``00XX`` and ``11XX`` do not match any of the
        same keys (i.e., they do not intersect)::
            >>> intersect(0b0000, 0b1100, 0b1100, 0b1100)
            False
        :param key_a: key of the first key-mask pair
        :type key_a: int
        :param mask_a: mask of the first key-mask pair
        :type mask_a: int
        :param key_b: key of the second key-mask pair
        :type key_b: int
        :param mask_b: mask of the second key-mask pair
        :type mask_b: int
        :return: True if and only if there is an intersection
        """
        return (key_a & mask_b) == (key_b & mask_a)

    def merge(self, entry1, entry2):
        """
        Merges two entries/triples into one that covers both

        The assumption is that they both have the same known spinnaker_route

        :param entry1: Key, Mask, defaultable from the first entry
        :type entry1: Entry
        :param entry2: Key, Mask, defaultable from the second entry
        :type entry2: Entry
        :return: Key, Mask, defaultable from merged entry
        :rtype: (int, int, bool)
        """
        any_ones = entry1.key | entry2.key
        all_ones = entry1.key & entry2.key
        all_selected = entry1.mask & entry2.mask

        # Compute the new mask  and key
        any_zeros = ~all_ones
        new_xs = any_ones ^ any_zeros
        mask = all_selected & new_xs  # Combine existing and new Xs
        key = all_ones & mask
        return key, mask, entry1.defaultable and entry2.defaultable

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
            self._all_entries.append(Entry(
                entry.routing_entry_key, entry.mask, entry.defaultable,
                entry.spinnaker_route))
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

        # convert the results back to a routing table
        compressed_table = MulticastRoutingTable(
            router_table.x, router_table.y)
        index = 0
        while index < self._write_index:
            entry = self._all_entries[index]
            m = MulticastRoutingEntry(
                entry.key, entry.mask, defaultable=entry.defaultable,
                spinnaker_route=entry.spinnaker_route)
            compressed_table.add_multicast_routing_entry(m)
            index += 1
        return compressed_table

    def compress_tables(self, router_tables, progress):
        """
        Compress all the unordered routing tables

        Tables who start of smaller than target_length are not compressed

        :param router_tables: Routing tables
        :type router_tables: MulticastRoutingTables
        :param progress: Progress bar to show while working
        :tpye progress: ProgressBar
        :return: The compressed but still unordered routing tables
        """
        compressed_tables = MulticastRoutingTables()
        for table in progress.over(router_tables.routing_tables):
            if table.number_of_entries < self._target_length:
                compressed_table = table
            else:
                compressed_table = self.compress_table(table)
            compressed_tables.add_routing_table(compressed_table)

        return compressed_tables
