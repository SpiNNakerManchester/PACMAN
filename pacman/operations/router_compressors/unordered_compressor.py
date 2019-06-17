from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)
from pacman.model.routing_tables.multicast_routing_tables import (from_json, to_json)
from spinn_machine import MulticastRoutingEntry
import json


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
    any_ones = entry1.routing_entry_key | entry2.routing_entry_key
    all_ones = entry1.routing_entry_key & entry2.routing_entry_key
    all_selected = entry1.mask & entry2.mask

    # Compute the new mask  and key
    any_zeros = ~all_ones
    new_xs = any_ones ^ any_zeros
    mask = all_selected & new_xs  # Combine existing and new Xs
    key = all_ones & mask
    return MulticastRoutingEntry(key, mask, entry1.processor_ids, entry2.link_ids, entry1.defaultable and entry2.defaultable)


def find_merge(entry1, entry2, unchecked):
    m1 = merge(entry1, entry2)
    for check in unchecked:
        if intersect(m1.routing_entry_key, m1.mask, check.routing_entry_key, check.mask):
            return None
    return m1

def compress_by_route(to_check, unchecked):
    unmergable = []
    while len(to_check) > 1:
        entry = to_check.pop()
        for other in to_check:
            merged = find_merge(entry, other, unchecked)
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
    unchecked = []
    spinnaker_routes = set()
    for entry in router_table.multicast_routing_entries:
        unchecked.append(entry)
        spinnaker_routes.add(entry.spinnaker_route)

    for spinnaker_route in spinnaker_routes:
        to_check = []
        for i in range(len(unchecked) - 1, -1, -1):
            entry = unchecked[i]
            if entry.spinnaker_route == spinnaker_route:
                del unchecked[i]
                to_check.append(entry)

        for entry in compress_by_route(to_check, unchecked):
            compressed_table.add_multicast_routing_entry(entry)
            unchecked.append(entry)
    print(router_table.number_of_entries, len(spinnaker_routes), compressed_table.number_of_entries)
    return compressed_table

def compare(uncompressed, compressed):
    for uncomp in uncompressed.multicast_routing_entries:
        found = False
        for comp in compressed.multicast_routing_entries:
            if intersect(uncomp.routing_entry_key, uncomp.mask, comp.routing_entry_key, comp.mask):
                assert uncomp.spinnaker_route == comp.spinnaker_route, "{}{}".format(uncomp,comp)
                assert set(uncomp.processor_ids) == set(comp.processor_ids)
                found = True
        assert found, uncomp

def compress_tables(router_tables):
    compressed_tables = MulticastRoutingTables()
    for table in router_tables:
        print(table.number_of_entries)
        if table.number_of_entries < 7000:
            compressed_table = table
        else:
            compressed_table = compress_table(table)
            compare(table, compressed_table)
            compressed_dict = codify_table(compressed_table)
            for o_route in table.multicast_routing_entries:
                compare_route(o_route, compressed_dict)
        compressed_tables.add_routing_table(compressed_table)

    return compressed_tables

from pacman.exceptions import PacmanRoutingException

WILDCARD = "*"
LINE_FORMAT = "0x{:08X} 0x{:08X} 0x{:08X} {: <7s} {}\n"


def codify(route, length=32):
    """
    This method discovers all the routing keys covered by this route.

    Starts of with the assumption that the key is always covered.

    Whenever a mask bit is zero the list of covered keys is doubled to\
    include both the key with a zero and a one at that place.

    :param route: single routing Entry
    :type route: :py:class:`spinn_machine.MulticastRoutingEntry`
    :param length: length in bits of the key and mask (defaults to 32)
    :type length: int
    :return: set of routing_keys covered by this route
    :rtype: str
    """
    mask = route.mask
    key = route.routing_entry_key
    code = ""
    # Check each bit in the mask
    for i in range(length):
        bit_value = 2**i
        # If the mask bit is zero then both zero and one acceptable
        if mask & bit_value:
            code = str(int(key & bit_value != 0)) + code
        else:
            # Safety key 1 with mask 0 is an error
            assert key & bit_value == 0, \
                "Bit {} on the mask:{} is 0 but 1 in the key:{}".format(
                    i, bin(mask), bin(key))
            code = WILDCARD + code
    return code

try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict

def codify_table(table, length=32):
    code_dict = OrderedDict()
    for route in table.multicast_routing_entries:
        code_dict[codify(route, length)] = route
    return code_dict


def covers(o_code, c_code):
    if o_code == c_code:
        return True
    for o_char, c_char in zip(o_code, c_code):
        if o_char == "1" and c_char == "0":
            return False
        if o_char == "0" and c_char == "1":
            return False
        # o_char = c_char or either wildcard is some cover
    return True


def calc_remainders(o_code, c_code):
    if o_code == c_code:
        # "" = "" so also the terminator case
        return []
    remainders = []
    for tail in calc_remainders(o_code[1:], c_code[1:]):
        remainders.append(o_code[0] + tail)
    if o_code[0] == WILDCARD:
        if c_code[0] == "0":
            remainders.append("1" + o_code[1:])
        if c_code[0] == "1":
            remainders.append("0" + o_code[1:])
    return remainders


def compare_route(o_route, compressed_dict, o_code=None, start=0):
    if o_code is None:
        o_code = codify(o_route)
    keys = list(compressed_dict.keys())
    for i in range(start, len(keys)):
        c_code = keys[i]
        if covers(o_code, c_code):
            c_route = compressed_dict[c_code]
            #if o_route.defaultable != c_route.defaultable:
            #    raise PacmanRoutingException(
            #        "Compressed route {} covers original route {} but has "
            #        "a different defaultable value.".format(c_route, o_route))
            if set(o_route.processor_ids) != set(c_route.processor_ids):
                print(o_code)
                print(c_code)
                raise PacmanRoutingException(
                    "Compressed route {} {} covers original route {} {} but has "
                    "a different processor_ids.".format(c_route, c_code, o_route, o_code))
            if set(o_route.link_ids) != set(c_route.link_ids):
                print(o_code)
                print(c_code)
                raise PacmanRoutingException(
                    "Compressed route {} covers original route {} but has "
                    "a different link_ids.".format(c_route, o_route))
            remainders = calc_remainders(o_code, c_code)
            for remainder in remainders:
                compare_route(o_route, compressed_dict, o_code=remainder,
                              start=i + 1)
            return
        compare_route(o_route, compressed_dict, o_code=o_code, start=i+1)
        return


if __name__ == '__main__':
    router_tables = from_json("D:\spinnaker\my_spinnaker\malloc_routing_tables.json")
    #router_tables = from_json("small_routing_tables.json")
    compressed = compress_tables(router_tables)
    with open("compressed_routing_tables.json", "w") as f:
        json.dump(to_json(compressed), f)

    """
    proc_ids = range(18)
    link_ids = range(6)
    entry1 = MulticastRoutingEntry(0, 4294967232, proc_ids, link_ids, True)
    entry2 = MulticastRoutingEntry(64, 4294967232, proc_ids, link_ids, True)
    merge(entry1, entry2, [])
    """