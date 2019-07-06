from __future__ import print_function
try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
from pacman.exceptions import PacmanRoutingException

WILDCARD = "*"


def calc_length(original, compressed):
    max_key = 0
    for route in original.multicast_routing_entries:
        max_key = max(max_key, route.mask, route.routing_entry_key)
    for route in compressed.multicast_routing_entries:
        max_key = max(max_key, route.mask, route.routing_entry_key)
    return max_key


def codify(route, length=32):
    """
    This method discovers all the routing keys covered by this route

    Starts of with the assumption that the key is always covered.

    Whenever a mask bit is zero the list of covered keys is doubled to\
        include both the key with a aero and a one at that place

    :param route: single routing Entry
    :type route: :py:class:`spinn_machine.MulticastRoutingEntry`
    :param length: length in bits of the key and mask
    :type length: int
    :return: set of routing_keys covered by this route
    """
    mask = route.mask
    routing_entry_key = route.routing_entry_key
    code = ""
    # Check each bit in the mask
    for i in range(length):
        bit_value = 2**i
        if mask & bit_value:
            if routing_entry_key & bit_value == 0:
                code = "0" + code
            else:
                code = "1" + code
        else:
            # If the mask bit is zero then both zero and one acceptable
            # Safety key 1 with mask 0 is an error
            assert routing_entry_key & bit_value != 1, \
                "Bit {} on the mask:{} is 0 but 1 in the key:{}".format(
                    i, bin(mask), bin(routing_entry_key))
            code = WILDCARD + code
    return code


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
        print(o_code, start, i, len(keys))
        c_code = keys[i]
        if covers(o_code, c_code):
            print(o_code, c_code)  # TODO: Don't print this message!
            #print("covers")  # TODO: Don't print this message!
            c_route = compressed_dict[c_code]
            if not o_route.defaultable and c_route.defaultable:
                raise PacmanRoutingException(  # TODO: Raise this exception!
                    "Compressed route {} covers original route {} but has "
                    "a different defaultable value.".format(c_route, o_route))
            if o_route.processor_ids != c_route.processor_ids:
                if set(o_route.processor_ids) != set(c_route.processor_ids):
                    raise PacmanRoutingException(  # TODO: Raise this exception!
                        "Compressed route {} covers original route {} but has "
                        "a different processor_ids.".format(c_route, o_route))
            if o_route.link_ids != c_route.link_ids:
                if set(o_route.link_ids) != set(c_route.link_ids):
                    raise PacmanRoutingException(  # TODO: Raise this exception!
                        "Compressed route {} covers original route {} but has "
                        "a different link_ids.".format(c_route, o_route))
            remainders = calc_remainders(o_code, c_code)
            if len(remainders) > 0:
                print("remainders")
                print(remainders)  # TODO: Don't print this message!
            for remainder in remainders:
                compare_route(o_route, compressed_dict, o_code=remainder,
                              start=i + 1)
            return
    raise PacmanRoutingException("No route found {}".format(o_route))

def compare_tables(original, compressed):
    compressed_dict = codify_table(compressed)
    for o_route in original.multicast_routing_entries:
        compare_route(o_route, compressed_dict)
