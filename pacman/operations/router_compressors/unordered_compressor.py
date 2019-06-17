try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)
from pacman.model.routing_tables.multicast_routing_tables import (from_json, to_json)
from spinn_machine import MulticastRoutingEntry
import json

MAX_SUPPORTED_LENGTH = 1023


def intersect(key_a, mask_a, key_b, mask_b):
    """Return if key-mask pairs intersect (i.e., would both match some of the
    same keys).
    For example, the key-mask pairs ``00XX`` and ``001X`` both match the keys
    ``0010`` and ``0011`` (i.e., they do intersect)::
        >>> intersect(0b0000, 0b1100, 0b0010, 0b1110)
        True
    But the key-mask pairs ``00XX`` and ``11XX`` do not match any of the same
    keys (i.e., they do not intersect)::
        >>> intersect(0b0000, 0b1100, 0b1100, 0b1100)
        False
    Parameters
    ----------
    key_a : int
    mask_a : int
        The first key-mask pair
    key_b : int
    mask_b : int
        The second key-mask pair
    Returns
    -------
    bool
        True if the two key-mask pairs intersect otherwise False.
    """
    return (key_a & mask_b) == (key_b & mask_a)


def merge(entry1, entry2):
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

def find_merge(entry1, entry2, spinnaker_route, all_entries):
    m_key, m_mask, defaultable  = merge(entry1, entry2)
    for check_route in all_entries:
        if check_route != spinnaker_route:
            for c_key, c_mask, _ in all_entries[check_route]:
                if intersect(c_key, c_mask, m_key, m_mask):
                    return None
    return m_key, m_mask, defaultable

def compress_by_route(to_check, spinnaker_route, all_entries):
    unmergable = []
    while len(to_check) > 1:
        entry = to_check.pop()
        for other in to_check:
            merged = find_merge(entry, other, spinnaker_route, all_entries)
            if merged is not None:
                to_check.remove(other)
                to_check.append(merged)
                break
        if merged is None:
            unmergable.append(entry)
    unmergable.append(to_check.pop())
    return unmergable

def compress_table(router_table):
    compressed_table = MulticastRoutingTable(router_table.x, router_table.y)
    all_entries = defaultdict(list)
    spinnaker_routes = set()
    for entry in router_table.multicast_routing_entries:
        all_entries[entry.spinnaker_route].append((entry.routing_entry_key, entry.mask, entry.defaultable))
        spinnaker_routes.add(entry.spinnaker_route)

    length = router_table.number_of_entries
    for spinnaker_route in spinnaker_routes:
        if length > MAX_SUPPORTED_LENGTH:
            to_check = all_entries[spinnaker_route]
            length -= len(to_check)
            compressed = compress_by_route(to_check, spinnaker_route, all_entries)
            length += len(compressed)
            all_entries[spinnaker_route] = compressed
        else:
            compressed = all_entries[spinnaker_route]

    for spinnaker_route in spinnaker_routes:
        for key, mask, defaultable in all_entries[spinnaker_route]:
            compressed_table.add_multicast_routing_entry(
                MulticastRoutingEntry(key, mask, defaultable= defaultable,
                                      spinnaker_route=spinnaker_route))
    print(router_table.number_of_entries, len(spinnaker_routes), compressed_table.number_of_entries)
    return compressed_table


def compress_tables(router_tables):
    compressed_tables = MulticastRoutingTables()
    for table in router_tables:
        print(table.number_of_entries)
        if table.number_of_entries < 3000: # MAX_SUPPORTED_LENGTH:
            compressed_table = table
        else:
            compressed_table = compress_table(table)
        compressed_tables.add_routing_table(compressed_table)

    return compressed_tables


from pacman.operations.algorithm_reports.routing_compression_checker_report \
    import generate_routing_compression_checker_report

if __name__ == '__main__':
    router_tables = from_json("D:\spinnaker\my_spinnaker\malloc_routing_tables.json")
    #router_tables = from_json("small_routing_tables.json")
    compressed = compress_tables(router_tables)
    generate_routing_compression_checker_report("", router_tables, compressed)
    with open("compressed_routing_tables.json", "w") as f:
        json.dump(to_json(compressed), f)

