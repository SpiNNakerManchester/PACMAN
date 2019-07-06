try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict
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
    
    """

    __slots__ = [
        # Dict (by spinnaker_route) (for current chip)
        #   of entries represented as (key, mask, defautible)
        "_all_entries",
        # Max length below which the algorithm should stop compressing
        "_target_length",
        "_write_pointer",
        "_max_index",
        "_previous_pointer",
        "_remaining_pointer"

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

    def three_way_partition(self, low, high):
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

    def quicksort(self, low, high):
        if low < high:
            left, right = self.three_way_partition(low, high)
            self.quicksort(low, left - 1)
            self.quicksort(right, high)

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
        :type entry1: (int, int, bool)
        :param entry2: Key, Mask, defaultable from the second entry
        :type entry2: (int, int, bool)
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


    def find_merge(self, left, index):
        m_key, m_mask, defaultable = self.merge(
            self._all_entries[left], self._all_entries[index])
        check = 0
        while check < self._previous_pointer:
            if self.intersect(
                    self._all_entries[check].key, self._all_entries[check].mask,
                    m_key, m_mask):
                return False
            check += 1
        check = self._remaining_pointer
        while check < self._max_index:
            if self.intersect(
                    self._all_entries[check].key, self._all_entries[check].mask,
                    m_key, m_mask):
                return False
            check += 1
        self._all_entries[left] = Entry(
            m_key, m_mask, defaultable, self._all_entries[left].spinnaker_route)
        return True

    def compress_by_route(self, left, right):
        while left < right:
            index = left + 1
            while index <= right:
                merged = self.find_merge(left, index)
                if merged:
                    self._all_entries[index] = self._all_entries[right]
                    # Setting None not needed but easier when debugging
                    # self._all_entries[right] = None
                    right -= 1
                    break

                index += 1
            if not merged:
                self._all_entries[self._write_pointer] = self._all_entries[left]
                self._write_pointer += 1
                left += 1
        if left == right:
            self._all_entries[self._write_pointer] = self._all_entries[left]
            # Setting None not needed but easier when debugging
            # if left != self._write_pointer:
            #    self._all_entries[left] = None
            self._write_pointer += 1

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
        self.quicksort(0, len(self._all_entries)-1)

        self._write_pointer = 0
        self._max_index = len(self._all_entries) - 1
        self._previous_pointer = 0
        ""
        left = 0
        while left < self._max_index:
            right = left
            while (right < len(self._all_entries) - 1 and
                   self._all_entries[right+1].spinnaker_route
                   == self._all_entries[left].spinnaker_route):
                right += 1
            self._remaining_pointer = right + 1
            self.compress_by_route(left, right)
            left = right + 1
            self._previous_pointer = self._write_pointer

        # convert the results back to a routing table
        compressed_table = MulticastRoutingTable(
            router_table.x, router_table.y)
        index = 0
        while index < self._write_pointer:
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
