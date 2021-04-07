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
from pacman.utilities.constants import FULL_MASK
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables.compressed_multicast_routing_table import (
    CompressedMulticastRoutingTable)
from pacman.model.routing_tables import MulticastRoutingTables
from pacman.exceptions import PacmanRoutingException
logger = FormatAdapter(logging.getLogger(__file__))


class MallocBasedRouteMerger(object):
    """ Routing table entry merging function, that merges based off a\
        malloc memory style.
    """

    __slots__ = []

    def __call__(self, router_tables):
        """
        :param MulticastRoutingTables router_tables:
        :rtype: MulticastRoutingTables
        :raises PacmanRoutingException:
        """
        tables = MulticastRoutingTables()

        progress = ProgressBar(
            len(router_tables.routing_tables) * 2,
            "Compressing Routing Tables")

        # Create all masks without holes
        allowed_masks = [FULL_MASK - ((2 ** i) - 1) for i in range(33)]

        # Check that none of the masks have "holes" e.g. 0xFFFF0FFF has a hole
        for router_table in router_tables.routing_tables:
            for entry in router_table.multicast_routing_entries:
                if entry.mask not in allowed_masks:
                    raise PacmanRoutingException(
                        "Only masks without holes are allowed in tables for"
                        " MallocBasedRouteMerger (disallowed mask={})".format(
                            hex(entry.mask)))

        for router_table in progress.over(router_tables.routing_tables):
            new_table = self._merge_routes(router_table)
            tables.add_routing_table(new_table)
            n_entries = sum(
                not entry.defaultable
                for entry in new_table.multicast_routing_entries)
            logger.info("Reduced from {} to {}",
                        len(router_table.multicast_routing_entries), n_entries)
            if n_entries > 1023:
                raise PacmanRoutingException(
                    "Cannot make table small enough: {} entries".format(
                        n_entries))
        return tables

    def _merge_routes(self, router_table):
        """
        :param MulticastRoutingTable router_table:
        :rtype: MulticastRoutingTable
        """
        merged_routes = CompressedMulticastRoutingTable(
            router_table.x, router_table.y)
        # Order the routes by key
        entries = sorted(
            router_table.multicast_routing_entries,
            key=lambda entry: entry.routing_entry_key)

        # Find adjacent entries that can be merged
        pos = 0
        last_key_added = 0
        while pos < len(entries):
            links = entries[pos].link_ids
            processors = entries[pos].processor_ids
            next_pos = pos + 1

            # Keep going until routes are not the same or too many keys are
            # generated
            base_key = int(entries[pos].routing_entry_key)
            while (next_pos < len(entries) and
                    entries[next_pos].link_ids == links and
                    entries[next_pos].processor_ids == processors and
                    (base_key & entries[next_pos].routing_entry_key) >
                    last_key_added):
                base_key = (
                    base_key & entries[next_pos].routing_entry_key)
                next_pos += 1
            next_pos -= 1

            # logger.info("Pre decision {}", hex(base_key))

            # If there is something to merge, merge it if possible
            merge_done = False
            if next_pos != pos:

                # logger.info("At merge, base_key = {}", hex(base_key))

                # Find the next nearest power of 2 to the number of keys
                # that will be covered
                last_key = (
                    entries[next_pos].routing_entry_key +
                    (~entries[next_pos].mask & FULL_MASK))
                n_keys = (1 << (last_key - base_key).bit_length()) - 1
                n_keys_mask = ~n_keys & FULL_MASK
                base_key = base_key & n_keys_mask
                if ((base_key + n_keys) >= last_key and
                        base_key > last_key_added and
                        (next_pos + 1 >= len(entries) or
                         entries[pos].routing_entry_key + n_keys <
                         entries[next_pos + 1].routing_entry_key)):
                    last_key_added = base_key + n_keys
                    merged_routes.add_multicast_routing_entry(
                        MulticastRoutingEntry(
                            int(base_key), n_keys_mask,
                            processors, links, defaultable=False))
                    pos = next_pos
                    merge_done = True

            if not merge_done:
                merged_routes.add_multicast_routing_entry(entries[pos])
                last_key_added = (
                    entries[pos].routing_entry_key +
                    (~entries[pos].mask & FULL_MASK))
            pos += 1

        return merged_routes
