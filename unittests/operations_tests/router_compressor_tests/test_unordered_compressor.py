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

from __future__ import print_function
try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
import unittest
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)
from pacman.operations.router_compressors.unordered_compressor import (
    UnorderedCompressor)
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
        c_code = keys[i]
        print(o_code, c_code)  # TODO: Don't print this message!
        if covers(o_code, c_code):
            print("covers")  # TODO: Don't print this message!
            c_route = compressed_dict[c_code]
            if o_route.defaultable != c_route.defaultable:
                PacmanRoutingException(  # TODO: Raise this exception!
                    "Compressed route {} covers original route {} but has "
                    "a different defaultable value.".format(c_route, o_route))
            if o_route.processor_ids != c_route.processor_ids:
                PacmanRoutingException(  # TODO: Raise this exception!
                    "Compressed route {} covers original route {} but has "
                    "a different processor_ids.".format(c_route, o_route))
            if o_route.link_ids != c_route.link_ids:
                PacmanRoutingException(  # TODO: Raise this exception!
                    "Compressed route {} covers original route {} but has "
                    "a different link_ids.".format(c_route, o_route))
            remainders = calc_remainders(o_code, c_code)
            print(remainders)  # TODO: Don't print this message!
            for remainder in remainders:
                compare_route(o_route, compressed_dict, o_code=remainder,
                              start=i + 1)
            return
        compare_route(o_route, compressed_dict, o_code=o_code, start=i+1)
        return


def compare_table(original, compressed):
    compressed_dict = codify_table(compressed)
    print(compressed_dict)  # TODO: Don't print this message!
    print("-------------")  # TODO: Don't print this message!
    for o_route in original.multicast_routing_entries:
        compare_route(o_route, compressed_dict)


class MyTestCase(unittest.TestCase):

    def test(self):
        """Test minimising a table of the form:

            0000 -> N NE
            0001 -> E
            0101 -> SW
            1000 -> N NE
            1001 -> E
            1110 -> SW
            1100 -> N NE
            0X00 -> S SW

        The result (worked out by hand) should be:

            0000 -> N NE
            0X00 -> S SW
            1X00 -> N NE
            X001 -> E
            X1XX -> SW
        """

        original_tables = MulticastRoutingTables()
        original_table = MulticastRoutingTable(x=0, y=0)
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0000, 0b1111, [1, 2], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0001, 0b1111, [0], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0101, 0b1111, [4], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1000, 0b1111, [1, 2], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1001, 0b1111, [0], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1110, 0b1111, [4], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1100, 0b1111, [1, 2], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0000, 0b1011, [4, 5], [], False))
        original_tables.add_routing_table(original_table)

        mundy_compressor = UnorderedCompressor()
        compressed_tables = mundy_compressor(original_tables)
        compressed_table = compressed_tables.get_routing_table_for_chip(0, 0)

        # TODO: FIX THIS SO THAT WE TEST THAT THE RESULT IS VALID
        # result_table_expected = MulticastRoutingTable(x=0, y=0)
        # result_table_expected.add_multicast_routing_entry(
        #     MulticastRoutingEntry(0b0000, 0b1111, [1, 2], [], False))
        # result_table_expected.add_multicast_routing_entry(
        #     MulticastRoutingEntry(0b0000, 0b1011, [4, 5], [], False))
        # result_table_expected.add_multicast_routing_entry(
        #     MulticastRoutingEntry(0b1000, 0b1011, [1, 2], [], False))
        # result_table_expected.add_multicast_routing_entry(
        #     MulticastRoutingEntry(0b0001, 0b0111, [0], [], False))
        # result_table_expected.add_multicast_routing_entry(
        #     MulticastRoutingEntry(0b0100, 0b0100, [4], [], False))

        # Minimise as far as possible
        assert compressed_table.number_of_entries == 5
        # assert compressed_table == result_table_expected
        compare_table(original_table, compressed_table)


if __name__ == '__main__':
    unittest.main()
