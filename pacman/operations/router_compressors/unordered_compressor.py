try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)
from spinn_machine import MulticastRoutingEntry



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

    Another optimisation is that instead of saving entries in the buckets
    Save just triples of key, mask and defaultable
        (spinneker_route is assigned at the bucket level)
    Then create entries at the end using the tuples
    """

    __slots__ = [
        # Dict (by spinnaker_route) (for current chip)
        #   of entries represented as (key, mask, defautible)
        "_all_entries",
        # Max length below which the algorithm should stop compressing
        "_target_length"
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
        key1, mask1, defaultable1 = entry1
        key2, mask2, defaultable2 = entry2
        any_ones = key1 | key2
        all_ones = key1 & key2
        all_selected = mask1 & mask2

        # Compute the new mask  and key
        any_zeros = ~all_ones
        new_xs = any_ones ^ any_zeros
        mask = all_selected & new_xs  # Combine existing and new Xs
        key = all_ones & mask
        return key, mask, defaultable1 and defaultable2

    def find_merge(self, entry1, entry2, spinnaker_route):
        """
        Creates and check the merge between the two entries

        If legal the merge is returned otherwise None

        :param entry1: Key, Mask, defaultable from the first entry
        :type entry1: (int, int, bool)
        :param entry2: Key, Mask, defaultable from the second entry
        :type entry2: (int, int, bool)
        :param spinnaker_route: The route shared by both entries
        :type spinnaker_route: int
        :return: Key, Mask, defaultable from checked merged entry or None
        :rtype: (int, int, bool)
        """
        m_key, m_mask, defaultable = self.merge(entry1, entry2)
        for check_route in self._all_entries:
            if check_route != spinnaker_route:
                for c_key, c_mask, _ in self._all_entries[check_route]:
                    if self.intersect(c_key, c_mask, m_key, m_mask):
                        return None
        return m_key, m_mask, defaultable

    def compress_by_route(self, to_check, spinnaker_route):
        """
        Compresses (if possible) the entries for a single spinnaker_route

        :param to_check: List of (Key, Mask, defaultable) from each entry with
            this spinnaker_route
        :type entry1: [(int, int, bool)]
        :param spinnaker_route: The route shared by all to_check entries
        :type spinnaker_route: int
        :return: (Key, Mask, defaultable) for each entry in the compressed list
        :rtype: [(int, int, bool)]
        """
        results = []
        while len(to_check) > 1:
            entry = to_check.pop()
            for other in to_check:
                merged = self.find_merge(entry, other, spinnaker_route)
                if merged is not None:
                    to_check.remove(other)
                    to_check.append(merged)
                    break
            if merged is None:
                results.append(entry)
        results.append(to_check.pop())
        return results

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
        self._all_entries = defaultdict(list)
        spinnaker_routes = set()
        for entry in router_table.multicast_routing_entries:
            self._all_entries[entry.spinnaker_route].append(
                (entry.routing_entry_key, entry.mask, entry.defaultable))
            spinnaker_routes.add(entry.spinnaker_route)

        # Process the buckets one at a time keeping track of total length
        length = router_table.number_of_entries
        for spinnaker_route in spinnaker_routes:
            if length > self._target_length:
                to_check = self._all_entries[spinnaker_route]
                length -= len(to_check)
                compressed = self.compress_by_route(to_check, spinnaker_route)
                length += len(compressed)
                self._all_entries[spinnaker_route] = compressed
            else:
                break

        # convert the results back to a routing table
        compressed_table = MulticastRoutingTable(
            router_table.x, router_table.y)
        for spinnaker_route in spinnaker_routes:
            for key, mask, defaultable in self._all_entries[spinnaker_route]:
                compressed_table.add_multicast_routing_entry(
                    MulticastRoutingEntry(key, mask, defaultable=defaultable,
                                          spinnaker_route=spinnaker_route))
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
