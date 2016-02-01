from pacman.model.routing_tables.multicast_routing_table\
    import MulticastRoutingTable
from pacman.model.routing_tables.multicast_routing_tables\
    import MulticastRoutingTables
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry

import numpy


class BasicRouteMerger(object):

    def __call__(self, router_tables):
        tables = MulticastRoutingTables()
        merge_masks = numpy.array(
            sorted(range(0, 0xF8), key=lambda x: bin(x).count("1")))
        merge_masks <<= 8
        for router_table in router_tables.routing_tables:
            new_table = self.merge_routes(router_table, merge_masks)
            if len(new_table.multicast_routing_entries) > 1023:
                raise Exception("Could not compress table enough")
            tables.add_routing_table(new_table)
        return {'routing_tables': tables}

    @staticmethod
    def merge_routes(router_table, merge_masks):
        merged_routes = MulticastRoutingTable(router_table.x, router_table.y)
        keys_merged = set()

        entries = router_table.multicast_routing_entries
        for router_entry in entries:
            if router_entry.routing_entry_key in keys_merged:
                continue

            # print "key =", hex(router_entry.routing_entry_key)

            mask = router_entry.mask
            if mask == 0xFFFFF800:
                merge_done = False

                for extra_bits in merge_masks:

                    new_mask = 0xFFFF0000 | extra_bits
                    # print "trying mask =", hex(new_mask), hex(extra_bits)

                    masked_key = router_entry.routing_entry_key & new_mask

                    # Check that all the cores on this chip have the same route
                    # as this is the only way we can merge here
                    mergable = True
                    potential_merges = set()
                    for router_entry_2 in entries:
                        # if key2 in keys_merged:
                        #     continue

                        masked_key2 = (
                            router_entry_2.routing_entry_key & new_mask)

                        if (masked_key == masked_key2 and (
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
                        elif masked_key == masked_key2:
                            # print(
                            #     "    ", hex(key), "and", hex(key2),
                            #     "can be merged")
                            potential_merges.add(router_entry_2)

                    if mergable and len(potential_merges) > 1:
                        # print ("Merging", [
                        #     hex(route.routing_entry_key)
                        #     for route in potential_merges], "using mask =",
                        #     hex(new_mask), "and key =", hex(masked_key),
                        #     "and route =", router_entry.processor_ids,
                        #     router_entry.link_ids)

                        # if masked_key in merged_routes:
                        #     raise Exception(
                        #         "Attempting to merge an existing key")
                        merged_routes.add_mutlicast_routing_entry(
                            MulticastRoutingEntry(
                                masked_key, new_mask,
                                router_entry.processor_ids,
                                router_entry.link_ids, defaultable=False))
                        keys_merged.update([
                            route.routing_entry_key
                            for route in potential_merges])
                        merge_done = True
                        break

                if not merge_done:
                    # print "Was not able to merge", hex(key)
                    merged_routes.add_mutlicast_routing_entry(router_entry)
            else:
                merged_routes.add_mutlicast_routing_entry(router_entry)
        return merged_routes
