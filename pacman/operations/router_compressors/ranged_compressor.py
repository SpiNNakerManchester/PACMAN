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

import logging
import sys
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import Machine, MulticastRoutingEntry
from pacman.data import PacmanDataView
from pacman.model.routing_tables import (
    CompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.exceptions import MinimisationFailedError

logger = FormatAdapter(logging.getLogger(__name__))


def range_compressor(accept_overflow=True):
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
    router_tables = PacmanDataView.get_uncompressed()
    progress = ProgressBar(len(router_tables.routing_tables), message)
    compressor = RangeCompressor()
    compressed_tables = MulticastRoutingTables()
    for table in progress.over(router_tables.routing_tables):
        new_table = compressor.compress_table(table)
        if (new_table.number_of_entries > Machine.ROUTER_ENTRIES and
                not accept_overflow):
            raise MinimisationFailedError(
                f"The routing table {table.x} {table.y} with "
                f"{table.number_of_entries} entries after compression "
                f"still has {new_table.number_of_entries} so will not fit")
        compressed_tables.add_routing_table(new_table)
    logger.info(f"Ranged compressor resulted with the largest table of size "
                f"{compressed_tables.max_number_of_entries}")
    return compressed_tables


class RangeCompressor(object):
    """

    """

    __slots__ = [
        # Router table to add merged rutes into
        "_compressed",
        # List of entries to be merged
        "_entries"
    ]

    def __init__(self):
        self._compressed = None
        self._entries = None

    def compress_table(self, uncompressed):
        """ Compresses all the entries for a single table.

        Compressed the entries for this unordered table
        returning a new table with possibly fewer entries

        :param UnCompressedMulticastRoutingTable uncompressed:
            Original Routing table for a single chip
        :return: Compressed routing table for the same chip
        :rtype: list(Entry)
        """
        # Check you need to compress
        if not get_config_bool(
                "Mapping", "router_table_compress_as_far_as_possible"):
            if uncompressed.number_of_entries < Machine.ROUTER_ENTRIES:
                return uncompressed

        # Step 1 get the entries and make sure they are sorted by key
        self._entries = list(uncompressed.multicast_routing_entries)
        self._entries.sort(key=lambda x: x.routing_entry_key)
        if not self._validate():
            return uncompressed

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
        self._merge_range(first, i)  # pylint:disable=undefined-loop-variable

        # return the results as a list
        return self._compressed

    def _validate(self):
        for i in range(len(self._entries)):
            if self._get_endpoint(i) >= self._get_key(i+1):
                logger.warning(
                    "Unable to run range compressor because entries overlap")
                return False
        return True

    def _get_key(self, index):
        """
        Gets routing_entry_key for entry index with support for index overflow

        if index == len(self._entries):
            return sys.maxsize
        :param int index:
        """
        if index == len(self._entries):
            return sys.maxsize
        entry = self._entries[index]
        return entry.routing_entry_key & entry.mask

    def _get_endpoint(self, index):
        """
        Get the end of the range covered by entry index's key and mask

        With support for index underflow

        :param index:
        :return:
        """
        if index < 0:
            return 0
        entry = self._entries[index]
        # return the key plus the mask flipping ones and zeros
        return (entry.routing_entry_key | ~entry.mask) & 0xFFFFFFFF

    def _merge_range(self, first, last):
        # With a range of 1 just use the existing
        if first == last:
            self._compressed.add_multicast_routing_entry(self._entries[first])
            return

        # Find the points the range must cover
        first_point = self._get_key(first)
        last_point = self._get_endpoint(last)
        # Find the points the range may NOT go into
        pre_point = self._get_endpoint(first-1)
        post_point = self._get_key(last+1)

        # find the power big enough to include the first and last enrty
        dif = last_point - first_point
        power = self.next_power(dif)

        # Find the start range cutoffs
        low_cut = first_point // power * power
        high_cut = low_cut + power

        # If that does not cover all try one power higher
        if high_cut < last_point:
            power <<= 1
            low_cut = first_point // power * power
            high_cut = low_cut + power

        # The power is too big if it touches the entry before or after
        while power > 1 and (low_cut < pre_point or high_cut > post_point):
            power >>= 1
            low_cut = first_point // power * power
            high_cut = low_cut + power

        # The range may now not cover all the index so reduce the indexes
        full_last = last
        while high_cut <= last_point:
            last -= 1
            last_point = self._get_endpoint(last)

        # make the new router entry
        new_mask = 2 ** 32 - power
        route = self._entries[first].spinnaker_route
        new_entry = MulticastRoutingEntry(
            low_cut, new_mask,  spinnaker_route=route)
        self._compressed.add_multicast_routing_entry(new_entry)

        # Do any indexes skip from before
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
