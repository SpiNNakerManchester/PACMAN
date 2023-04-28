# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_machine import Machine
from pacman.exceptions import PacmanElementAllocationException
from .abstract_compressor import AbstractCompressor
from .entry import Entry


def pair_compressor(ordered=True, accept_overflow=False, verify=False):
    """
    :param bool accept_overflow:
        A flag which should only be used in testing to stop raising an
        exception if result is too big
    :param bool verify: If set to true will verify the length before returning
    :rtype: MulticastRoutingTables
    """
    compressor = _PairCompressor(ordered, accept_overflow)
    # pylint:disable=protected-access
    compressed = compressor._run()
    # TODO currenly normal pari compressor does not verify lengths
    if verify:
        verify_lengths(compressed)
    return compressed


def verify_lengths(compressed):
    """
    :param MulticastRoutingTables compressed:
    :raises PacmanElementAllocationException:
        if the compressed table won't fit
    """
    problems = ""
    for table in compressed:
        if table.number_of_entries > Machine.ROUTER_ENTRIES:
            problems += f"(x:{table.x},y:{table.y})={table.number_of_entries} "
    if len(problems) > 0:
        raise PacmanElementAllocationException(
            "The routing table after compression will still not fit"
            f" within the machines router: {problems}")


class _PairCompressor(AbstractCompressor):
    """
    Routing Table compressor based on brute force.
    Finds mergable pairs to replace.

    This algorithm assumes unordered routing tables and returns
    a possibly ordered routing tables. If unordered it can be used
    as a precompressor for another that makes use of order.

    In the simplest format the algorithm is:

    #. For every pair of entries in the table

       #. If they have the same spinnaker_route

          #. Create a merged entry
          #. Check that does not intersect any entry with a different route

             #. Remove the two original entries
             #. Add the merged entry
             #. Start over

    A slightly optimised algorithm is:

    #. Split the entries into buckets based on spinnaker route
    #. Process the buckets one at a time

       #. For each entry in the buckets

          #. For each other entry in the bucket

             #. Create a merge entry
             #. Make sure there is no clash with an entry in another bucket
             #. Replace the two entries and add the merge
             #. Start the bucket over

          #. If no merge found move the entry from the bucket to the result\
             list

       #. When the bucket is empty the result list becomes the bucket

    A farther optimisation is to do the whole thing in place in a single list:

    #. Step 1 is sort the list by route in place
    #. Step 2 do the compression route by route using indexes into the array

       #. The array is split into 6 parts.

          #. 0 to _previous_pointer(-1): \
            Entries in buckets that have already been compressed
          #. _previous_pointer to _write_pointer(-1): \
            Finished entries for the current bucket
          #. _write_pointer to left(-1): \
            Unused space due to previous merges
          #. left to right: \
            Not yet finished entries from the current bucket
          #. right(+ 1) to _remaining_index(-1): \
            Unused space due to previous merges
          #. _remaining_index to max_index(-1): \
            Entries in buckets not yet compressed

    #. Step 3 use only the entries up to _write_pointer(-1)

    A farther optimisation is to uses order.
    The entries are sorted by route frequency from low to high.
    The results are considered ordered so previous routes are not
    considered.

    The advantage is this allows all the entries from the most frequent
    route to be merged into a single entry. And the second most
    frequent only has to consider the most frequent routes.

    Step 1 requires the counting of the frequency of routes and the
    sorting the routes based on this frequency.
    The current tie break between routes with the same frequency is
    the route but this is arbitrary at the algorithm level.
    This code does not use a dictionary to keep the code the same as
    the C.

    Step 2 is change in that the previous entries
    (0 to _previous_pointer(-1)) are not considered for clash checking
    """

    __slots__ = [
        # A list of all entries which may be sorted
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
        # C does not support dict so to get the histogram we use arrays
        # In python a dict implementation is only marginally faster so not used
        # to keep c and python code as similar as possible
        # List of the routes to match with the frequencies
        "_routes",
        # List of the frequencies. Match index for index with routes
        "_routes_frequency",
        # Number of unique routes found so far
        "_routes_count",
    ]

    def __init__(self, ordered=True, accept_overflow=False):
        super().__init__(ordered, accept_overflow)
        self._all_entries = None
        self._write_index = None
        self._max_index = None
        self._previous_index = None
        self._remaining_index = None
        self._routes = None
        self._routes_frequency = None
        self._routes_count = None

    def _compare_routes(self, route_a, route_b):
        """
        Compares two routes for sorting based on the frequency of each route.

        The assumption here is that self._routes has been sorted with the
        highest frequency at the top of the tables.

        So stop as soon as 1 of the routes is found.

        For two different routes but with the same frequency order is based on
        the (currently arbitrary) order they are in the self._routes table

        :param int route_a:
        :param int route_b:
        :return: ordering value (-1, 0, 1)
        :rtype: int
        """
        if route_a == route_b:
            return 0
        for i in range(self._routes_count):
            if self._routes[i] == route_a:
                return 1
            if self._routes[i] == route_b:
                return -1
        raise PacmanElementAllocationException("Sorting error")

    def _three_way_partition_table(self, low, high):
        """
        Partitions the entries between low and high into three parts

        based on: https://en.wikipedia.org/wiki/Dutch_national_flag_problem

        :param int low: Inclusive Lowest index to consider
        :param int high: Inclusive Highest index to consider
        :return: (last_index of lower, last_index_of_middle)
        :rtype: tuple(int,int)
        """
        check = low + 1
        pivot = self._all_entries[low].spinnaker_route
        while check <= high:
            compare = self._compare_routes(
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
        Sorts the entries in place based on frequency of their route

        :param int low: Inclusive lowest index to consider
        :param int high: Inclusive highest index to consider
        """
        if low < high:
            left, right = self._three_way_partition_table(low, high)
            self._quicksort_table(low, left - 1)
            self._quicksort_table(right, high)

    def _swap_routes(self, index_a, index_b):
        """
        Helper function to swap *both* the routes and routes frequency tables

        :param int index_a:
        :param int index_b:
        """
        temp = self._routes_frequency[index_a]
        self._routes_frequency[index_a] = self._routes_frequency[index_b]
        self._routes_frequency[index_b] = temp
        temp = self._routes[index_a]
        self._routes[index_a] = self._routes[index_b]
        self._routes[index_b] = temp

    def _three_way_partition_routes(self, low, high):
        """
        Partitions the routes and frequencies into three parts.

        based on: https://en.wikipedia.org/wiki/Dutch_national_flag_problem

        :param int low: Lowest index to consider
        :param int high: Highest index to consider
        :return: (last_index of lower, last_index_of_middle)
        :rtype: tuple(int,int)
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
        Sorts the routes in place based on frequency.

        :param int low: Inclusive lowest index to consider
        :param int high: Inclusive highest index to consider
        """
        if low < high:
            left, right = self._three_way_partition_routes(low, high)
            self._quicksort_routes(low, left - 1)
            self._quicksort_routes(right, high)

    def _find_merge(self, left, index):
        """
        Attempt to find a merge between the left entry and the index entry.

        Creates a merge and then checks it does not intersect with entries
        with different routes.

        If no intersect detected entry[left] is replaced with the merge

        :param int left: Index of Entry to merge and replace if possible
        :param int index: Index of entry to merge with
        :return: True if and only if a merge was found and done
        :rtype: bool
        """
        m_key, m_mask, defaultable = self.merge(
            self._all_entries[left], self._all_entries[index])
        if not self.ordered:
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
        Compresses the entries between left and right.

        :param int left: Inclusive index of first entry to merge
        :param int right: Inclusive index of last entry to merge
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
        """
        :param int route:
        """
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
        returning a new table with possibly fewer entries

        The resulting table may be ordered or unordered depending on the
        value of ordered passed into the initialisation method.
        Ordered tables may be shorted than unordered ones.

        :param UnCompressedMulticastRoutingTable router_table:
            Original Routing table for a single chip
        :return: Compressed routing table for the same chip
        :rtype: list(Entry)
        """

        # Split the entries into buckets based on spinnaker_route
        self._all_entries = []
        self._routes_count = 0
        # Imitate creating fixed size arrays
        self._routes = Machine.ROUTER_ENTRIES * [None]
        self._routes_frequency = Machine.ROUTER_ENTRIES * [None]

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

        while left <= self._max_index:
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

    @staticmethod
    def intersect(key_a, mask_a, key_b, mask_b):
        """
        Return if key-mask pairs intersect (i.e., would both match some of
        the same keys).

        For example, the key-mask pairs ``00XX`` and ``001X`` both match the
        keys ``0010`` and ``0011`` (i.e., they do intersect)::

            >>> intersect(0b0000, 0b1100, 0b0010, 0b1110)
            True

        But the key-mask pairs ``00XX`` and ``11XX`` do not match any of the
        same keys (i.e., they do not intersect)::

            >>> intersect(0b0000, 0b1100, 0b1100, 0b1100)
            False

        :param int key_a: The key of first key-mask pair
        :param int mask_a: The mask of first key-mask pair
        :param int key_b: The key of second key-mask pair
        :param int mask_b: The mask of second key-mask pair
        :return: True if the two key-mask pairs intersect otherwise False.
        :rtype: bool
        """
        return (key_a & mask_b) == (key_b & mask_a)

    def merge(self, entry1, entry2):
        """
        Merges two entries/triples into one that covers both.

        The assumption is that they both have the same known spinnaker_route

        :param ~pacman.operations.router_compressors.Entry entry1:
            Key, Mask, defaultable from the first entry
        :param ~pacman.operations.router_compressors.Entry entry2:
            Key, Mask, defaultable from the second entry
        :return: Key, Mask, defaultable from merged entry
        :rtype: tuple(int, int, bool)
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

    @property
    def ordered(self):
        return self._ordered
