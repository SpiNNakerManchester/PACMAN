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
from typing import Dict, List, Optional, TextIO
from spinn_utilities.log import FormatAdapter
from spinn_machine import MulticastRoutingEntry
from pacman.exceptions import PacmanRoutingException
from pacman.model.routing_tables import AbstractMulticastRoutingTable
from pacman.utilities.algorithm_utilities.routes_format import format_route

logger = FormatAdapter(logging.getLogger(__name__))
WILDCARD = "*"
LINE_FORMAT = "0x{:08X} 0x{:08X} 0x{:08X} {: <7s} {}\n"


def codify(route: MulticastRoutingEntry, length: int = 32) -> str:
    """
    This method discovers all the routing keys covered by this route.

    Starts of with the assumption that the key is always covered.

    Whenever a mask bit is zero the list of covered keys is doubled to
    include both the key with a zero and a one at that place.

    :param route: single routing entry
    :param length: length in bits of the key and mask (defaults to 32)
    :return: set of routing_keys covered by this route
    """
    mask = route.mask
    key = route.key
    # Check for validity: key 1 with mask 0 is an error
    bad = key & ~mask
    if bad:
        logger.error(
            "Bit {} on the mask:{} is 0 but 1 in the key:{}",
            # Magic to find first set bit: See
            # https://stackoverflow.com/a/36059264/301832
            (bad & -bad).bit_length(), bin(mask), bin(key))

    # Check each bit in the mask; use bit from key if so, else WILDCARD
    return "".join(
        str(int(key & bit != 0) if (mask & bit) else WILDCARD)
        for bit in map(lambda i: 1 << i, reversed(range(length))))


def codify_table(
        table: AbstractMulticastRoutingTable, length: int = 32) -> Dict[
            str, MulticastRoutingEntry]:
    """
    Apply :py:func:`codify` to all entries in a table.

    :param table:
    :param length:
    :return: mapping from codified route to routing entry
    """
    return {
        codify(route, length): route
        for route in table.multicast_routing_entries}


def _covers(o_code: str, c_code: str) -> bool:
    """
    :param o_code:
    :param c_code:
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


def _calc_remainders(o_code: str, c_code: str) -> List[str]:
    """
    :param o_code: Codified original route
    :param c_code: Codified compressed route
    """
    if o_code == c_code:
        # "" = "" so also the terminator case
        return []
    remainders = []
    for tail in _calc_remainders(o_code[1:], c_code[1:]):
        remainders.append(o_code[0] + tail)
    if o_code[0] == WILDCARD:
        if c_code[0] == "0":
            remainders.append("1" + o_code[1:])
        if c_code[0] == "1":
            remainders.append("0" + o_code[1:])
    return remainders


def compare_route(
        o_route: MulticastRoutingEntry,
        compressed_dict: Dict[str, MulticastRoutingEntry],
        o_code: Optional[str] = None, start: int = 0,
        f: Optional[TextIO] = None) -> None:
    """
    Compare that the compressed route is correct.

    :param o_route: the original route
    :param compressed_dict: Compressed routes
    :param o_code: Codified original route (if known)
    :param start: Starting index in compressed routes
    :param f: Where to write (part of) the route report
    """
    if o_code is None:
        o_code = codify(o_route)
    keys = list(compressed_dict.keys())
    for i in range(start, len(keys)):
        c_code = keys[i]
        if _covers(o_code, c_code):
            c_route = compressed_dict[c_code]
            if f is not None:
                f.write(f"\t\t{format_route(c_route)}\n")
            if o_route.processor_ids != c_route.processor_ids:
                raise PacmanRoutingException(
                    f"Compressed route {c_route} covers original route "
                    f"{o_route} but has a different processor_ids.")
            if o_route.link_ids != c_route.link_ids:
                raise PacmanRoutingException(
                    f"Compressed route {c_route} covers original route "
                    f"{o_route} but has a different link_ids.")
            if not o_route.defaultable and c_route.defaultable:
                if o_route == c_route:
                    raise PacmanRoutingException(
                        f"Compressed route {c_route} while original route "
                        f"{o_route} but has a different defaultable value.")
                compare_route(o_route, compressed_dict, o_code=o_code,
                              start=i + 1, f=f)
            else:
                remainders = _calc_remainders(o_code, c_code)
                for remainder in remainders:
                    compare_route(o_route, compressed_dict, o_code=remainder,
                                  start=i + 1, f=f)
            return
    if not o_route.defaultable:
        # print(f"No route found {o_route}")
        raise PacmanRoutingException(f"No route found {o_route}")


def compare_tables(
        original: AbstractMulticastRoutingTable,
        compressed: AbstractMulticastRoutingTable) -> None:
    """
    Compares the two tables without generating any output.

    :param original: The original routing tables
    :param compressed:
        The compressed routing tables.
        Which will be considered in order.
    :raises: PacmanRoutingException if there is any error
    """
    compressed_dict = codify_table(compressed)
    for o_route in original.multicast_routing_entries:
        compare_route(o_route, compressed_dict)
