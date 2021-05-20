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

from collections import OrderedDict
import logging
import os
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
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
    code_dict = OrderedDict()
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


def generate_routing_compression_checker_report(
        report_folder, routing_tables, compressed_routing_tables):
    """ Make a full report of how the compressed covers all routes in the\
        and uncompressed routing table

    :param str report_folder: the folder to store the resulting report
    :param MulticastRoutingTables routing_tables: the original routing tables
    :param MulticastRoutingTables compressed_routing_tables:
        the compressed routing tables
    :rtype: None
    """
    file_name = os.path.join(
        report_folder, "routing_compression_checker_report.rpt")

    try:
        with open(file_name, "w") as f:
            progress = ProgressBar(
                routing_tables.routing_tables,
                "Generating routing compression checker report")
            f.write("If this table did not raise an exception compression "
                    "was fully checked. \n\n")
            f.write("The format is:\n"
                    "Chip x, y\n"
                    "\t Uncompressed Route\n"
                    "\t\tCompressed Route\n\n")

            for original in progress.over(routing_tables.routing_tables):
                x = original.x
                y = original.y
                f.write("Chip: X:{} Y:{} \n".format(x, y))

                compressed_table = compressed_routing_tables.\
                    get_routing_table_for_chip(x, y)
                compressed_dict = codify_table(compressed_table)
                for o_route in original.multicast_routing_entries:
                    f.write("\t{}\n".format(format_route(o_route)))
                    compare_route(o_route, compressed_dict, f=f)
    except IOError:
        logger.exception("Generate_router_comparison_reports: Can't open file"
                         " {} for writing.", file_name)
