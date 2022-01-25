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

import logging
import sys
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import Machine, MulticastRoutingEntry
from pacman.model.routing_tables import (
    CompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.exceptions import MinimisationFailedError

logger = FormatAdapter(logging.getLogger(__name__))


def range_compressor(router_tables, accept_overflow=True):
    """

    :param MulticastRoutingTables router_tables:
    :param bool accept_overflow:
        A flag which should only be used in testing to stop raising an
        exception if result is too big
    :rtype: MulticastRoutingTables
    """
    if accept_overflow:
        message = "Precompressing tables using Range Compressor"
    else:
        message = "Compressing tables using Range Compressor"
    max_length = 0
    progress = ProgressBar(len(router_tables.routing_tables), message)
    compressor = RangeCompressor()
    compressed_tables = MulticastRoutingTables()
    for table in progress.over(router_tables.routing_tables):
        new_table = compressor.compress_table(table)
        if new_table.number_of_entries > max_length:
            max_length = new_table.number_of_entries
            if (new_table.number_of_entries > Machine.ROUTER_ENTRIES and
                    not accept_overflow):
                raise MinimisationFailedError(
                    f"The routing table {table.x} {table.y} with "
                    f"{table.number_of_entries} entries after compression "
                    f"still has {new_table.number_of_entries} so will not fit")
        compressed_tables.add_routing_table(new_table)
    logger.info(f"Ranged compressor resulted with the largest table of size "
                f"{max_length}")
    return compressed_tables, max_length


class RangeCompressor(object):
    """

    """

    __slots__ = [
        # Router table to add merged rutes into
        "_compressed",
        # List of entries to be merged
        "_entries"
    ]

    def compress_table(self, uncompressed):
        """ Compresses all the entries for a single table.

        Compressed the entries for this unordered table
        returning a new table with possibly fewer entries

        :param UnCompressedMulticastRoutingTable uncompressed:
            Original Routing table for a single chip
        :return: Compressed routing table for the same chip
        :rtype: list(Entry)
        """
        # TODO Verify that none of the masks have holes.

        # Step 1 get the entries and make sure they are sorted by key
        self._entries = uncompressed.multicast_routing_entries
        self._entries.sort(key=lambda x: x.routing_entry_key)

        # Step 2 Create the results Table
        self._compressed = CompressedMulticastRoutingTable(
            uncompressed.x, uncompressed.y)

        # Step 3 Find ranges of entries with the same route and merge them
        # Start the first range
        route = self._entries[0].spinnaker_route
        first = 0
        for i, entry in enumerate(self._entries):
            # Keep building the range until the route changes
            if entry.spinnaker_route != route:
                # Merge all the entries in the range
                self._merge_range(first, i-1)
                # Start the next range with this entry
                first = i
                route = entry.spinnaker_route
        # Merge the last range
        self._merge_range(first, i)

        # return the results as a list
        return self._compressed

    def _get_key(self, index):
        if index < 0:
            return 0
        if index == len(self._entries):
            return sys.maxsize
        return self._entries[index].routing_entry_key

    def _merge_range(self, first, last):
        if first == last:
            self._compressed.add_multicast_routing_entry(self._entries[first])
            return

        # find the power big enough to include the first and last enrty
        first_key = self._entries[first].routing_entry_key
        last_key = self._entries[last].routing_entry_key
        dif = last_key - first_key
        power = self.next_power(dif)

        low_cut = self.cut_off(first_key, power)
        pre_key = self._get_key(first - 1)
        while low_cut < pre_key and power > 1:
            power //= 2
            low_cut = self.cut_off(first_key, power)
        post_key = self._get_key(last + 1)
        high_cut = low_cut + power
        while high_cut > post_key and power > 1:
            power //= 2
            low_cut = self.cut_off(first_key, power)
            high_cut = low_cut + power
        full_last = last
        while high_cut <= last_key:
            last -= 1
            last_key = self._get_key(last)
        new_mask = 2 ** 32 - power
        route = self._entries[first].spinnaker_route
        new_entry = MulticastRoutingEntry(
            low_cut, new_mask,  spinnaker_route=route)
        self._compressed.add_multicast_routing_entry(new_entry)
        if full_last != last:
            self._merge_range(last + 1, full_last)

    @staticmethod
    def next_power(number):
        power = 1
        while power < number:
            power *= 2
        return power

    @staticmethod
    def cut_off(key, power):
        return key // power * power
