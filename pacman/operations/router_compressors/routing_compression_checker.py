# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from spinn_utilities.log import FormatAdapter
from pacman.exceptions import PacmanRoutingException
from pacman.utilities.algorithm_utilities.routes_format import format_route

logger = FormatAdapter(logging.getLogger(__name__))
WILDCARD = "*"
LINE_FORMAT = "0x{:08X} 0x{:08X} 0x{:08X} {: <7s} {}\n"


def codify(route, length=32):
    """
    This method discovers all the routing keys covered by this route.

    Starts of with the assumption that the key is always covered.

    Whenever a mask bit is zero the list of covered keys is doubled to\
    include both the key with a zero and a one at that place.

    :param ~spinn_machine.MulticastRoutingEntry route: single routing Entry
    :param int length: length in bits of the key and mask (defaults to 32)
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


def codify_table(table, length=32):
    """
    :param MulticastRoutingTable table:
    :param int length:
    :rtype: dict(str, ~spinn_machine.MulticastRoutingEntry)
    """
    code_dict = dict()
    for route in table.multicast_routing_entries:
        code_dict[codify(route, length)] = route
    return code_dict


def covers(o_code, c_code):
    """
    :param str o_code:
    :param str c_code:
    :rtype: bool
    """
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
    """
    :param str o_code:
    :param str c_code:
    :rtype: list(str)
    """
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


def compare_route(o_route, compressed_dict, o_code=None, start=0, f=None):
    """
    :param ~spinn_machine.MulticastRoutingEntry o_route: the original route
    :param dict compressed_dict:
    :param str o_code:
    :param int start:
    :param ~io.FileIO f:
    :rtype: None
    """
    if o_code is None:
        o_code = codify(o_route)
    keys = list(compressed_dict.keys())
    for i in range(start, len(keys)):
        c_code = keys[i]
        if covers(o_code, c_code):
            c_route = compressed_dict[c_code]
            if f is not None:
                f.write("\t\t{}\n".format(format_route(c_route)))
            if o_route.processor_ids != c_route.processor_ids:
                if set(o_route.processor_ids) != set(c_route.processor_ids):
                    raise PacmanRoutingException(
                        "Compressed route {} covers original route {} but has "
                        "a different processor_ids.".format(c_route, o_route))
            if o_route.link_ids != c_route.link_ids:
                if set(o_route.link_ids) != set(c_route.link_ids):
                    raise PacmanRoutingException(
                        "Compressed route {} covers original route {} but has "
                        "a different link_ids.".format(c_route, o_route))
            if not o_route.defaultable and c_route.defaultable:
                if o_route == c_route:
                    raise PacmanRoutingException(
                        "Compressed route {} while original route {} but has "
                        "a different defaultable value.".format(
                            c_route, o_route))
                else:
                    compare_route(o_route, compressed_dict, o_code=o_code,
                                  start=i + 1, f=f)
            else:
                remainders = calc_remainders(o_code, c_code)
                for remainder in remainders:
                    compare_route(o_route, compressed_dict, o_code=remainder,
                                  start=i + 1, f=f)
            return
    if not o_route.defaultable:
        # print("No route found {}".format(o_route))
        raise PacmanRoutingException("No route found {}".format(o_route))


def compare_tables(original, compressed):
    """ Compares the two tables without generating any output

    :param MulticastRoutingTable original: The original routing tables
    :param MulticastRoutingTable compressed: The compressed routing tables.
        Which will be considered in order.
    :rtype: None
    :raises: PacmanRoutingException if there is any error
    """
    compressed_dict = codify_table(compressed)
    for o_route in original.multicast_routing_entries:
        compare_route(o_route, compressed_dict)
