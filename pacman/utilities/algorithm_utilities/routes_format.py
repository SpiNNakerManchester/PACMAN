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

import logging
import os
import time
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.log import FormatAdapter
from spinn_machine import Router
from pacman import exceptions
from pacman.model.graphs import AbstractSpiNNakerLink, AbstractFPGA
from pacman.model.graphs.common import EdgeTrafficType
#from pacman.operations.algorithm_reports.router_summary import RouterSummary

logger = FormatAdapter(logging.getLogger(__name__))


def _reduce_route_value(processors_ids, link_ids):
    """
    :param iterable(int) processors_ids:
    :param iterable(int) link_ids:
    :rtype: int
    """
    value = 0
    for link in link_ids:
        value += 1 << link
    for processor in processors_ids:
        value += 1 << (processor + 6)
    return value


def _expand_route_value(processors_ids, link_ids):
    """ Convert a 32-bit route word into a string which lists the target cores\
        and links.

    :param iterable(int) processors_ids:
    :param iterable(int) link_ids:
    :rtype: str
    """

    # Convert processor targets to readable values:
    route_string = "["
    separator = ""
    for processor in processors_ids:
        route_string += "{}{}".format(separator, processor)
        separator = ", "

    route_string += "] ["

    # Convert link targets to readable values:
    link_labels = {0: 'E', 1: 'NE', 2: 'N', 3: 'W', 4: 'SW', 5: 'S'}

    separator = ""
    for link in link_ids:
        route_string += "{}{}".format(separator, link_labels[link])
        separator = ", "
    route_string += "]"
    return route_string


def format_route(entry):
    """ How to render a single routing entry.

    :param ~spinn_machine.MulticastRoutingEntry entry:
    :rtype: str
    """
    line_format = "0x{:08X} 0x{:08X} 0x{:08X} {: <7s} {}"

    key = entry.routing_entry_key
    mask = entry.mask
    route = _reduce_route_value(entry.processor_ids, entry.link_ids)
    route_txt = _expand_route_value(entry.processor_ids, entry.link_ids)
    return line_format.format(key, mask, route, str(entry.defaultable),
                              route_txt)
