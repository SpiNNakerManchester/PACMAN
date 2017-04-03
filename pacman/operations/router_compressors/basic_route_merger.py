from pacman.model.routing_tables \
    import MulticastRoutingTable, MulticastRoutingTables

from spinn_machine.utilities.progress_bar import ProgressBar
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry


class BasicRouteMerger(object):
    """ functionality to merge routing tables entries via different masks and
    a exploration process

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
                    raise Exception(
                        "Only masks without holes are allowed in tables for"
                        " BasicRouteMerger (disallowed mask={})".format(
                            hex(entry.mask)))

        for router_table in router_tables.routing_tables:
            new_table = self._merge_routes(router_table, previous_masks)
            tables.add_routing_table(new_table)
            n_entries = len([
                entry for entry in new_table.multicast_routing_entries
                if not entry.defaultable])
            print "Reduced from {} to {}".format(
                len(router_table.multicast_routing_entries),
                n_entries)
            if n_entries > 1023:
                raise Exception(
                    "Cannot make table small enough: {} entries".format(
                        n_entries))
            progress.update()
        progress.end()
        return tables

    def _get_merge_masks(self, mask, previous_masks):
        if mask in previous_masks:
            return previous_masks[mask]

        last_one = 33 - bin(mask).rfind('1')
        n_bits = 16 - last_one
        merge_masks = sorted(
            [0xFFFF - ((2 ** n) - 1) for n in range(n_bits - 1, 17)],
            key=lambda x: bin(x).count("1"))

        # print hex(mask), [hex(m) for m in merge_masks]
        previous_masks[mask] = merge_masks
        return merge_masks

    def _merge_routes(self, router_table, previous_masks):
        merged_routes = MulticastRoutingTable(router_table.x, router_table.y)
        keys_merged = set()

        entries = router_table.multicast_routing_entries
        for router_entry in entries:
            if router_entry.routing_entry_key in keys_merged:
                continue

            # print "key =", hex(router_entry.routing_entry_key)

            mask = router_entry.mask
            if mask & 0xFFFF0000L == 0xFFFF0000L:
                merge_done = False

                for extra_bits in self._get_merge_masks(mask, previous_masks):

                    new_mask = 0xFFFF0000L | extra_bits
                    # print "trying mask =", hex(new_mask), hex(extra_bits)

                    new_key = router_entry.routing_entry_key & new_mask
                    new_n_keys = ~new_mask & 0xFFFFFFFFL
                    new_last_key = new_key + new_n_keys

                    # Check that all the cores on this chip have the same route
                    # as this is the only way we can merge here
                    mergable = True
                    potential_merges = set()
                    for router_entry_2 in entries:
                        key = router_entry_2.routing_entry_key
                        n_keys = ~router_entry_2.mask & 0xFFFFFFFFL
                        last_key = key + n_keys
                        masked_key = (
                            router_entry_2.routing_entry_key & new_mask)
                        overlap = (
                            min(new_last_key, last_key) -
                            max(new_key, key)) > 0
                        in_range = new_key <= key and new_last_key >= last_key

                        if (new_key == masked_key and (
                                not in_range or
                                (router_entry_2.routing_entry_key in
                                    keys_merged) or
                                (router_entry.processor_ids !=
                                    router_entry_2.processor_ids) or
                                (router_entry.link_ids !=
                                    router_entry_2.link_ids))):
                            # print(
                            #     "    ", hex(key), "and", hex(key2),
                            #     "have mismatched routes")
                            mergable = False
                            break
                        elif new_key == masked_key:
                            # print(
                            #     "    ", hex(key), "and", hex(key2),
                            #     "can be merged")
                            potential_merges.add(router_entry_2)
                        elif overlap:
                            mergable = False
                            break

                    if mergable and len(potential_merges) > 1:
                        # print("Merging", [
                        #     hex(route.routing_entry_key)
                        #     for route in potential_merges], "using mask =",
                        #     hex(new_mask), "and key =", hex(masked_key),
                        #     "and route =", router_entry.processor_ids,
                        #     router_entry.link_ids)

                        # if masked_key in merged_routes:
                        #     raise Exception(
                        #         "Attempting to merge an existing key")
                        merged_routes.add_multicast_routing_entry(
                            MulticastRoutingEntry(
                                new_key, new_mask,
                                router_entry.processor_ids,
                                router_entry.link_ids, defaultable=False))
                        keys_merged.update([
                            route.routing_entry_key
                            for route in potential_merges])
                        merge_done = True
                        break

                if not merge_done:
                    # print "Was not able to merge", hex(key)
                    merged_routes.add_multicast_routing_entry(router_entry)
                    keys_merged.add(router_entry.routing_entry_key)
            else:
                merged_routes.add_multicast_routing_entry(router_entry)
                keys_merged.add(router_entry.routing_entry_key)
        return merged_routes
