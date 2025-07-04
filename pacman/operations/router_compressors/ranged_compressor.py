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
from typing import cast, List
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry, RoutingEntry
from pacman.data import PacmanDataView
from pacman.model.routing_tables import (
    CompressedMulticastRoutingTable, MulticastRoutingTables,
    AbstractMulticastRoutingTable, UnCompressedMulticastRoutingTable)
from pacman.exceptions import MinimisationFailedError

logger = FormatAdapter(logging.getLogger(__name__))


def range_compressor(accept_overflow: bool = True) -> MulticastRoutingTables:
    """
    :param accept_overflow:
        A flag which should only be used in testing to stop raising an
        exception if result is too big
    """
    if accept_overflow:
        message = "Precompressing tables using Range Compressor"
    else:
        message = "Compressing tables using Range Compressor"
    router_tables = PacmanDataView.get_uncompressed()
    assert router_tables is not None
    progress = ProgressBar(len(router_tables.routing_tables), message)
    compressor = RangeCompressor()
    compressed_tables = MulticastRoutingTables()
    for table in progress.over(router_tables.routing_tables):
        new_table = compressor.compress_table(cast(
            UnCompressedMulticastRoutingTable, table))
        chip = PacmanDataView.get_chip_at(table.x, table.y)
        target = chip.router.n_available_multicast_entries
        if new_table.number_of_entries > target and not accept_overflow:
            raise MinimisationFailedError(
                f"The routing table {table.x} {table.y} with "
                f"{table.number_of_entries} entries after compression "
                f"still has {new_table.number_of_entries} so will not fit")
        compressed_tables.add_routing_table(new_table)
    logger.info(f"Ranged compressor resulted with the largest table of size "
                f"{compressed_tables.get_max_number_of_entries()}")
    return compressed_tables


class RangeCompressor(object):
    """
    A compressor based on ranges.
    Use via :py:func:`range_compressor`.
    """
    __slots__ = (
        # Router table to add merged routes into
        "_compressed",
        # List of entries to be merged
        "_entries")

    def __init__(self) -> None:
        # temp values to avoid Optional
        self._entries: List[MulticastRoutingEntry] = []
        self._compressed = CompressedMulticastRoutingTable(0, 0)

    def compress_table(
            self, uncompressed: UnCompressedMulticastRoutingTable
            ) -> AbstractMulticastRoutingTable:
        """
        Compresses all the entries for a single table.

        Compressed the entries for this unordered table
        returning a new table with possibly fewer entries

        :param uncompressed:
            Original Routing table for a single chip
        :return: Compressed routing table for the same chip
        """
        # Check you need to compress
        if not get_config_bool(
                "Mapping", "router_table_compress_as_far_as_possible"):
            chip = PacmanDataView.get_chip_at(uncompressed.x, uncompressed.y)
            target = chip.router.n_available_multicast_entries
            if uncompressed.number_of_entries < target:
                return uncompressed

        # Step 1 get the entries and make sure they are sorted by key
        self._entries = list(uncompressed.multicast_routing_entries)
        self._entries.sort(key=lambda x: x.key)
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

    def _validate(self) -> bool:
        for i in range(len(self._entries)):
            if self._get_endpoint(i) >= self._get_key(i+1):
                logger.warning(
                    "Unable to run range compressor because entries overlap")
                return False
        return True

    def _get_key(self, index: int) -> int:
        """
        Gets routing_entry_key for entry index with support for index overflow

        if index == len(self._entries):
            return sys.maxsize
        """
        if index == len(self._entries):
            return sys.maxsize
        entry = self._entries[index]
        return entry.key & entry.mask

    def _get_endpoint(self, index: int) -> int:
        """
        Get the end of the range covered by entry index's key and mask

        With support for index underflow
        """
        if index < 0:
            return 0
        entry = self._entries[index]
        # return the key plus the mask flipping ones and zeros
        return (entry.key | ~entry.mask) & 0xFFFFFFFF

    def _merge_range(self, first: int, last: int) -> None:
        while True:
            # With a range of 1 just use the existing
            if first == last:
                self._compressed.add_multicast_routing_entry(
                    self._entries[first])
                return

            # Find the points the range must cover
            first_point = self._get_key(first)
            last_point = self._get_endpoint(last)
            # Find the points the range may NOT go into
            pre_point = self._get_endpoint(first - 1)
            post_point = self._get_key(last + 1)

            # find the power big enough to include the first and last entry
            dif = last_point - first_point
            power = 1 if dif < 1 else 1 << ((dif - 1).bit_length())

            # Find the start range cut-off
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

            entry = RoutingEntry(spinnaker_route=route)
            self._compressed.add_multicast_routing_entry(MulticastRoutingEntry(
                low_cut, new_mask, entry))

            # Check if we're done
            if full_last == last:
                return
            # Loop to do any indexes skip from before
            first, last = last + 1, full_last
