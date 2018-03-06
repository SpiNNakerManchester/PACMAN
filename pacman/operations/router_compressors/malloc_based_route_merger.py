from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_tables \
    import MulticastRoutingTable, MulticastRoutingTables
from pacman.exceptions import PacmanRoutingException
from spinn_machine import MulticastRoutingEntry

import math


class MallocBasedRouteMerger(object):
    """ a routing table entry merging function, that merges based off a
    malloc memory style.

    """

    __slots__ = []

    def __call__(self, router_tables):
        tables = MulticastRoutingTables()
        previous_masks = dict()

        progress = ProgressBar(
            len(router_tables.routing_tables) * 2,
            "Compressing Routing Tables")

        # Create all masks without holes
        allowed_masks = [0xFFFFFFFFL - ((2 ** i) - 1) for i in range(33)]

        # Check that none of the masks have "holes" e.g. 0xFFFF0FFF has a hole
        for router_table in router_tables.routing_tables:
            for entry in router_table.multicast_routing_entries:
                if entry.mask not in allowed_masks:
                    raise PacmanRoutingException(
                        "Only masks without holes are allowed in tables for"
                        " MallocBasedRouteMerger (disallowed mask={})".format(
                            hex(entry.mask)))

        for router_table in progress.over(router_tables.routing_tables):
            new_table = self._merge_routes(router_table, previous_masks)
            tables.add_routing_table(new_table)
            n_entries = len([
                entry for entry in new_table.multicast_routing_entries
                if not entry.defaultable])
            print("Reduced from {} to {}".format(
                len(router_table.multicast_routing_entries),
                n_entries))
            if n_entries > 1023:
                raise PacmanRoutingException(
                    "Cannot make table small enough: {} entries".format(
                        n_entries))
        return tables

    def _merge_routes(self, router_table, previous_masks):
        merged_routes = MulticastRoutingTable(router_table.x, router_table.y)

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

            # print("Pre decision", hex(base_key))

            # If there is something to merge, merge it if possible
            merge_done = False
            if next_pos != pos:

                # print("At merge, base_key =", hex(base_key))

                # Find the next nearest power of 2 to the number of keys
                # that will be covered
                last_key = (
                    entries[next_pos].routing_entry_key +
                    (~entries[next_pos].mask & 0xFFFFFFFFL))
                n_keys = (last_key - base_key) + 1
                next_log_n_keys = int(math.ceil(math.log(n_keys, 2)))
                n_keys = (1 << next_log_n_keys) - 1
                n_keys_mask = ~n_keys & 0xFFFFFFFFL
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
                    (~entries[pos].mask & 0xFFFFFFFFL))
            pos += 1

        return merged_routes
