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
from pacman.utilities.constants import FULL_MASK
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables.compressed_multicast_routing_table import \
    CompressedMulticastRoutingTable
from pacman.model.routing_tables import MulticastRoutingTables
from pacman.exceptions import PacmanRoutingException

_UPPER_16_BITS = 0xFFFF << 16  # upper 16 bits of 32
_LOWER_16_BITS = 0xFFFF


class BasicRouteMerger(object):
    """ Merges routing tables entries via different masks and an\
        exploration process

    :param MulticastRoutingTables router_tables:
    :rtype: MulticastRoutingTables
    """

    __slots__ = []

    def __call__(self, router_tables):
        """
        :param MulticastRoutingTables router_tables:
        :rtype: MulticastRoutingTables
        """
        tables = MulticastRoutingTables()
        previous_masks = dict()

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
                        " BasicRouteMerger (disallowed mask={})".format(
                            hex(entry.mask)))

        for router_table in progress.over(router_tables.routing_tables):
            new_table = self._merge_routes(router_table, previous_masks)
            tables.add_routing_table(new_table)
            n_entries = sum(
                not entry.defaultable
                for entry in new_table.multicast_routing_entries)
            # print("Reduced from {} to {}".format(
            #     len(router_table.multicast_routing_entries), n_entries))
            if n_entries > 1023:
                raise PacmanRoutingException(
                    "Cannot make table small enough: {} entries".format(
                        n_entries))

        return tables

    def _get_merge_masks(self, mask, previous_masks):
        """
        :param int mask:
        :param dict(int,list(int)) previous_masks:
        :rtype: list(int)
        """
        if mask in previous_masks:
            return previous_masks[mask]

        last_one = 33 - bin(mask).rfind('1')
        n_bits = 16 - last_one
        merge_masks = sorted(
            [_LOWER_16_BITS - ((2 ** n) - 1) for n in range(n_bits - 1, 17)],
            key=lambda x: bin(x).count("1"))

        # print(hex(mask), [hex(m) for m in merge_masks])
        previous_masks[mask] = merge_masks
        return merge_masks

    def _merge_routes(self, router_table, previous_masks):
        """
        :param MulticastRoutingTable router_table:
        :param dict(int,list(int)) previous_masks:
        :rtype: MulticastRoutingTable
        """
        merged_routes = CompressedMulticastRoutingTable(
            router_table.x, router_table.y)
        keys_merged = set()

        entries = router_table.multicast_routing_entries
        for router_entry in entries:
            if router_entry.routing_entry_key in keys_merged:
                continue

            mask = router_entry.mask
            if mask & _UPPER_16_BITS == _UPPER_16_BITS:
                for extra_bits in self._get_merge_masks(mask, previous_masks):
                    new_mask = _UPPER_16_BITS | extra_bits
                    new_key = router_entry.routing_entry_key & new_mask
                    new_n_keys = ~new_mask & FULL_MASK

                    # Get candidates for this particular possible merge
                    potential_merges = self._mergeable_entries(
                        router_entry, entries, new_key, new_mask,
                        new_key + new_n_keys, keys_merged)

                    # Only do a merge if there's real merging to do
                    if len(potential_merges) > 1:
                        merged_routes.add_multicast_routing_entry(
                            MulticastRoutingEntry(
                                new_key, new_mask,
                                router_entry.processor_ids,
                                router_entry.link_ids, defaultable=False))
                        keys_merged.update(
                            route.routing_entry_key
                            for route in potential_merges)
                        break
                else:
                    # print("Was not able to merge", hex(key))
                    merged_routes.add_multicast_routing_entry(router_entry)
                    keys_merged.add(router_entry.routing_entry_key)
            else:
                merged_routes.add_multicast_routing_entry(router_entry)
                keys_merged.add(router_entry.routing_entry_key)
        return merged_routes

    def _mergeable_entries(
            self, entry, entries, new_key, new_mask, new_last_key, merged):
        """
        :param ~spinn_machine.MulticastRoutingEntry entry:
        :param iterable(~spinn_machine.MulticastRoutingEntry) entries:
        :param int new_key:
        :param int new_mask:
        :param int new_last_key:
        :param set(int) merged:
        :rtype: list(~spinn_machine.MulticastRoutingEntry)
        """
        # Check that all the cores on this chip have the same route as this is
        # the only way we can merge here
        potential_merges = set()
        for entry_2 in entries:
            key = entry_2.routing_entry_key
            n_keys = ~entry_2.mask & FULL_MASK
            last_key = key + n_keys
            masked_key = entry_2.routing_entry_key & new_mask
            overlap = (min(new_last_key, last_key) - max(new_key, key)) > 0
            in_range = new_key <= key and new_last_key >= last_key

            if (new_key == masked_key and (
                    not in_range
                    or entry_2.routing_entry_key in merged
                    or entry.processor_ids != entry_2.processor_ids
                    or entry.link_ids != entry_2.link_ids)):
                # Mismatched routes; cannot merge
                return []
            elif new_key == masked_key:
                # This one is mergeable
                potential_merges.add(entry_2)
            elif overlap:
                # Overlapping routes; cannot merge
                return []
        return potential_merges
