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


class PairCCompressor(AbstractCompressor):
    """
    Builds on UnorderedCompressor

    The difference here is that the buckets are sorted by size and compressed
    starting with the smallest.

    Previously merged buckets are ignored so this is an Order Dependent Version.

    Note this version used c style Objects only.
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
        "_remaining_index",
        "_routes",
        "_routes_count",
        "_routes_frequency"
    ]

    def _compare_routes_by_frequency(self, route_a, route_b):
        if route_a == route_b:
            return 0
        for i in range(self._routes_count):
            if self._routes[i] == route_a:
               return 1
            if self._routes[i] == route_b:
               return -1
        raise Exception("Apply Gibbs slap!")

    def _three_way_partition_table(self, low, high):
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
            compare = self._compare_routes_by_frequency(
                self._all_entries[check].spinnaker_route, pivot)
            if compare < 0:
                temp = self._all_entries[low]
                self._all_entries[low] = self._all_entries[check]
                self._all_entries[check] = temp
                low += 1
                check += 1
            elif compare > 0:
                temp = self._all_entries[high]
                self._all_entries[high] = self._all_entries[check]
                self._all_entries[check] = temp
                high -= 1
            else:
                check += 1
        return low, check

    def _quicksort_table(self, low, high):
        """
        Sorts the entries in place based on route
        :param low: Inclusive lowest index to consider
        :param high: Inclusive highest index to consider
        """
        if low < high:
            left, right = self._three_way_partition_table(low, high)
            self._quicksort_table(low, left - 1)
            self._quicksort_table(right, high)

    def _swap_routes(self, index_a, index_b):
        temp = self._routes_frequency[index_a]
        self._routes_frequency[index_a] = self._routes_frequency[index_b]
        self._routes_frequency[index_b] = temp
        temp = self._routes[index_a]
        self._routes[index_a] = self._routes[index_b]
        self._routes[index_b] = temp

    def _three_way_partition_routes(self, low, high):
        """
        Partitions the entries between low and high into three parts

        based on: https://en.wikipedia.org/wiki/Dutch_national_flag_problem
        :param low: Lowest index to consider
        :param high: Highest index to consider
        :return: (last_index of lower, last_index_of_middle)
        """
        check = low + 1
        pivot = self._routes_frequency[low]
        while check <= high:
            if self._routes_frequency[check] > pivot:
                self._swap_routes(low, check)
                low += 1
                check += 1
            elif self._routes_frequency[check] < pivot:
                self._swap_routes(high, check)
                high -= 1
            else:
                check += 1
        return low, check

    def _quicksort_routes(self, low, high):
        """
        Sorts the entries in place based on route
        :param low: Inclusive lowest index to consider
        :param high: Inclusive highest index to consider
        """
        if low < high:
            left, right = self._three_way_partition_routes(low, high)
            self._quicksort_routes(low, left - 1)
            self._quicksort_routes(right, high)

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
        #for check in range(self._previous_index):
        #    if self.intersect(
        #            self._all_entries[check].key,
        #            self._all_entries[check].mask,
        #            m_key, m_mask):
        #        return False
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

    def update_frequency(self, route):
        for i in range(self._routes_count):
            if self._routes[i] == route:
                self._routes_frequency[i] += 1
                return
        self._routes[self._routes_count] = route
        self._routes_frequency[self._routes_count] = 1
        self._routes_count += 1

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
        self._routes_count = 0
        # Imitate creating fixed size arrays
        self._routes = self.MAX_SUPPORTED_LENGTH * [None]
        self._routes_frequency = self.MAX_SUPPORTED_LENGTH * [None]

        for entry in router_table.multicast_routing_entries:
            self._all_entries.append(
                Entry.from_MulticastRoutingEntry(entry))
            self.update_frequency(entry.spinnaker_route)

        self._quicksort_routes(0, self._routes_count - 1)
        self._quicksort_table(0, len(self._all_entries) - 1)

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
